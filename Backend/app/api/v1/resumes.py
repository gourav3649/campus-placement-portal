from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pathlib import Path
import shutil
import json

from app.database import get_db
from app.api.deps import get_current_student
from app.models.student import Student
from app.models.resume import Resume
from app.schemas.resume import Resume as ResumeSchema, ResumeUploadResponse, ResumeWithParsedData
from app.core.config import get_settings
from app.utils.helpers import generate_unique_filename, sanitize_filename

router = APIRouter(prefix="/resumes", tags=["Resumes"])
settings = get_settings()

# Upload directory
UPLOAD_DIR = Path("uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def process_resume_background(resume_id: int, file_path: str, mime_type: str):
    """
    Background task to parse and process uploaded resume.
    
    Args:
        resume_id: ID of the resume record
        file_path: Path to uploaded file
        mime_type: MIME type of the file
    """
    from app.database import AsyncSessionLocal
    from app.services.resume_parser import ResumeParser
    from app.services.semantic_ranking import SemanticRankingService
    
    async with AsyncSessionLocal() as db:
        try:
            # Get resume record
            result = await db.execute(select(Resume).filter(Resume.id == resume_id))
            resume = result.scalar_one_or_none()
            
            if not resume:
                return
            
            # Update status to processing
            resume.parse_status = "processing"
            await db.commit()
            
            # Parse resume
            parser = ResumeParser()
            parsed_data = await parser.parse_resume(file_path, mime_type)
            
            # Generate embedding for semantic matching
            ranking_service = SemanticRankingService()
            profile_text = f"{parsed_data.get('summary', '')} {' '.join(parsed_data.get('skills', []))}"
            embedding = ranking_service.generate_embedding(profile_text)
            
            # Update resume with parsed data
            resume.raw_text = parsed_data.get("raw_text", "")
            resume.parsed_data = json.dumps(parsed_data)
            resume.extracted_skills = json.dumps(parsed_data.get("skills", []))
            resume.extracted_experience = json.dumps(parsed_data.get("experience", []))
            resume.extracted_education = json.dumps(parsed_data.get("education", []))
            resume.extracted_certifications = json.dumps(parsed_data.get("certifications", []))
            resume.embedding_vector = json.dumps(embedding)
            resume.parse_status = "completed"
            resume.parse_error = None
            
            await db.commit()
            
        except Exception as e:
            # Update status to failed
            if resume:
                resume.parse_status = "failed"
                resume.parse_error = str(e)
                await db.commit()
            print(f"Error processing resume {resume_id}: {str(e)}")


@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and parse a resume (PDF or DOCX).
    
    This endpoint:
    1. Validates file type and size
    2. Saves the file to disk
    3. Creates a database record
    4. Triggers background parsing using AI
    
    Requires: STUDENT role
    """
    # Validate file type
    allowed_types = settings.ALLOWED_RESUME_TYPES
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    # Generate unique filename
    original_filename = sanitize_filename(file.filename)
    unique_filename = generate_unique_filename(original_filename, prefix=f"student_{current_student.id}")
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file to disk
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Create resume record
    resume = Resume(
        student_id=current_student.id,
        filename=original_filename,
        file_path=str(file_path),
        file_size=file_size,
        mime_type=file.content_type,
        parse_status="pending"
    )
    
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    
    # Trigger background parsing
    background_tasks.add_task(
        process_resume_background,
        resume.id,
        str(file_path),
        file.content_type
    )
    
    return ResumeUploadResponse(
        resume_id=resume.id,
        filename=original_filename,
        file_size=file_size,
        parse_status="pending",
        message="Resume uploaded successfully. Processing in background."
    )


@router.get("/my", response_model=List[ResumeSchema])
async def get_my_resumes(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all resumes uploaded by current student.
    
    Requires: STUDENT role
    """
    result = await db.execute(
        select(Resume)
        .filter(Resume.student_id == current_student.id)
        .order_by(Resume.created_at.desc())
    )
    resumes = result.scalars().all()
    
    return resumes


@router.get("/{resume_id}", response_model=ResumeWithParsedData)
async def get_resume(
    resume_id: int,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific resume including parsed data.
    
    Requires: STUDENT role, must own the resume
    """
    result = await db.execute(
        select(Resume).filter(Resume.id == resume_id)
    )
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Check ownership
    if resume.student_id != current_student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this resume"
        )
    
    # Parse JSON fields for response
    response_data = ResumeWithParsedData(
        id=resume.id,
        student_id=resume.student_id,
        filename=resume.filename,
        file_path=resume.file_path,
        file_size=resume.file_size,
        mime_type=resume.mime_type,
        is_primary=resume.is_primary,
        parse_status=resume.parse_status,
        parse_error=resume.parse_error,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
        parsed_data=json.loads(resume.parsed_data) if resume.parsed_data else None,
        extracted_skills=json.loads(resume.extracted_skills) if resume.extracted_skills else None,
        extracted_experience=json.loads(resume.extracted_experience) if resume.extracted_experience else None,
        extracted_education=json.loads(resume.extracted_education) if resume.extracted_education else None,
        extracted_certifications=json.loads(resume.extracted_certifications) if resume.extracted_certifications else None
    )
    
    return response_data


@router.put("/{resume_id}/primary", response_model=ResumeSchema)
async def set_primary_resume(
    resume_id: int,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Set a resume as the primary resume for the student.
    
    Requires: STUDENT role, must own the resume
    """
    # Get the resume
    result = await db.execute(
        select(Resume).filter(Resume.id == resume_id)
    )
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Check ownership
    if resume.student_id != current_student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this resume"
        )
    
    # Unset all other resumes as primary
    all_resumes_result = await db.execute(
        select(Resume).filter(Resume.student_id == current_student.id)
    )
    all_resumes = all_resumes_result.scalars().all()
    
    for r in all_resumes:
        r.is_primary = False
    
    # Set this resume as primary
    resume.is_primary = True
    
    await db.commit()
    await db.refresh(resume)
    
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: int,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a resume.
    
    Requires: STUDENT role, must own the resume
    """
    result = await db.execute(
        select(Resume).filter(Resume.id == resume_id)
    )
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Check ownership
    if resume.student_id != current_student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this resume"
        )
    
    # Delete file from disk
    file_path = Path(resume.file_path)
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            print(f"Failed to delete file {file_path}: {str(e)}")
    
    # Delete from database
    await db.delete(resume)
    await db.commit()
    
    return None
