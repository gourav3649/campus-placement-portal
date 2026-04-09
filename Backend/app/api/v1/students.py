from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Any, Optional
import os
import logging
from datetime import datetime

from app.database import get_db
from app.models.student import Student
from app.models.resume import Resume
from app.schemas.student import StudentUpdate, StudentProfileResponse
from app.schemas.resume import ResumeResponse
from app.api.deps import get_current_student, get_current_placement_officer
from app.services.resume_parser import extract_resume_text
from app.services.embedding_service import (
    generate_embedding, 
    prepare_resume_text_for_embedding,
    embedding_from_json,
    EXPECTED_EMBEDDING_DIMENSION
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()

@router.get("/me", response_model=StudentProfileResponse)
async def get_my_profile(
    current_student: Student = Depends(get_current_student)
) -> Any:
    return current_student

@router.put("/me", response_model=StudentProfileResponse)
async def update_my_profile(
    student_in: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_student: Student = Depends(get_current_student)
) -> Any:
    update_data = student_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_student, field, value)
        
    db.add(current_student)
    await db.commit()
    await db.refresh(current_student)
    return current_student

@router.get("/", response_model=List[StudentProfileResponse])
async def list_students(
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer),
    skip: int = 0,
    limit: int = 100
) -> Any:
    # Officer can only see students in their college
    result = await db.execute(
        select(Student)
        .filter(Student.college_id == officer.college_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/resumes", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> Any:
    """
    Upload a resume file (PDF or DOCX).
    Automatically extracts text and generates embeddings.
    Validates data quality before storing.
    """
    logger.info(f"Resume upload started for student {student.id}, filename: {file.filename}")
    
    # Validate file type
    valid_content_types = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    if file.content_type not in valid_content_types:
        logger.warning(
            f"Invalid content type for student {student.id}: {file.content_type}. "
            f"Valid types: {', '.join(valid_content_types)}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Only PDF and DOCX files are supported. Got: {file.content_type}"
        )
    
    # Validate and read file
    try:
        file_content = await file.read()
        file_size = len(file_content)
    except Exception as e:
        logger.error(f"Failed to read uploaded file for student {student.id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Failed to read file. File may be corrupted."
        )
    
    # Validate file size
    if file_size == 0:
        logger.warning(f"Empty file uploaded by student {student.id}: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail="File is empty. Please upload a non-empty resume."
        )
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        logger.warning(
            f"File size exceeds limit for student {student.id}: "
            f"{file_size} > {settings.MAX_UPLOAD_SIZE}"
        )
        raise HTTPException(
            status_code=413,
            detail=f"File size {file_size} bytes exceeds maximum of {settings.MAX_UPLOAD_SIZE} bytes"
        )
    
    # Get and validate filename
    filename = file.filename
    if not filename:
        logger.error(f"No filename provided for student {student.id}")
        raise HTTPException(status_code=400, detail="Filename is required")
    
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in ('.pdf', '.docx'):
        logger.warning(
            f"Invalid file extension for student {student.id}: {file_ext}. "
            f"File: {filename}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"File must be PDF (.pdf) or DOCX (.docx). Got: {file_ext}"
        )
    
    # Create uploads directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Save file to disk
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    safe_filename = f"{student.id}_{timestamp}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    
    try:
        with open(file_path, 'wb') as f:
            f.write(file_content)
        logger.debug(f"Resume file saved for student {student.id}: {file_path}")
    except Exception as e:
        logger.error(f"Failed to write resume file to disk for student {student.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save file to server. Please try again."
        )
    
    # Extract resume text
    raw_text = None
    try:
        raw_text = await extract_resume_text(file_path)
        logger.debug(
            f"Resume text extracted for student {student.id}: "
            f"{len(raw_text)} chars from {filename}"
        )
    except ValueError as ve:
        logger.error(
            f"Resume extraction validation failed for student {student.id}: {str(ve)}"
        )
        try:
            os.remove(file_path)
        except:
            pass
        raise HTTPException(
            status_code=400,
            detail=f"Resume processing failed: {str(ve)}"
        )
    except Exception as e:
        logger.error(
            f"Resume extraction failed for student {student.id}: {str(e)}"
        )
        try:
            os.remove(file_path)
        except:
            pass
        raise HTTPException(
            status_code=400,
            detail="Failed to extract text from resume. File may be corrupted or image-based."
        )
    
    # Validate extracted text is not empty
    if not raw_text or not raw_text.strip():
        logger.error(f"No text extracted from resume for student {student.id}")
        try:
            os.remove(file_path)
        except:
            pass
        raise HTTPException(
            status_code=400,
            detail="No text could be extracted from the resume. Please ensure it contains readable text."
        )
    
    # Generate embedding from extracted text
    embedding_vector = None
    try:
        # Prepare text for embedding (validation included)
        normalized_text = prepare_resume_text_for_embedding(raw_text)
        
        # Generate embedding (validation includes dimension check)
        embedding_vector = generate_embedding(normalized_text)
        
        # Validate embedding was generated (extra safety check)
        if not embedding_vector:
            raise ValueError("Embedding generation returned empty result")
        
        logger.info(
            f"Resume embedding generated for student {student.id}: "
            f"text={len(normalized_text)} chars, embedding_json={len(embedding_vector)} chars"
        )
        
    except ValueError as ve:
        logger.error(
            f"Embedding generation failed for student {student.id}: {str(ve)}"
        )
        try:
            os.remove(file_path)
        except:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate embedding: {str(ve)}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error during embedding generation for student {student.id}: {str(e)}"
        )
        try:
            os.remove(file_path)
        except:
            pass
        raise HTTPException(
            status_code=500,
            detail="Failed to generate embedding. Please try again."
        )
    
    # Create Resume record in database
    try:
        db_resume = Resume(
            student_id=student.id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type,
            raw_text=raw_text,
            embedding_vector=embedding_vector,
        )
        db.add(db_resume)
        await db.commit()
        await db.refresh(db_resume)
        
        logger.info(
            f"Resume successfully uploaded and stored for student {student.id}: "
            f"resume_id={db_resume.id}, size={file_size} bytes"
        )
        return db_resume
        
    except Exception as e:
        logger.error(
            f"Failed to save resume record to database for student {student.id}: {str(e)}"
        )
        try:
            os.remove(file_path)
        except:
            pass
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save resume to database. Please try again."
        )


@router.get("/resumes", response_model=List[ResumeResponse])
async def list_my_resumes(
    db: AsyncSession = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> Any:
    """Get current student's uploaded resumes."""
    result = await db.execute(
        select(Resume)
        .filter(Resume.student_id == student.id)
        .order_by(Resume.uploaded_at.desc())
    )
    resumes = result.scalars().all()
    return resumes


@router.delete("/resumes/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: int,
    db: AsyncSession = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> None:
    """Delete a resume."""
    result = await db.execute(
        select(Resume).filter(Resume.id == resume_id, Resume.student_id == student.id)
    )
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Delete file from disk
    try:
        if os.path.exists(resume.file_path):
            os.remove(resume.file_path)
    except Exception as e:
        # Log but don't fail — database record cleanup is more important
        print(f"Warning: Failed to delete physical resume file: {str(e)}")
    
    # Delete database record
    await db.delete(resume)
    await db.commit()
