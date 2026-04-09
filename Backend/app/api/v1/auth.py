from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import Any

from app.database import get_db
from app.core.security import verify_password, hash_password, create_access_token, create_refresh_token
from app.core.rbac import Role
from app.models.user import User
from app.models.student import Student
from app.models.recruiter import Recruiter
from app.models.placement_officer import PlacementOfficer
from app.models.college import College
from app.schemas.user import UserCreate, Token, UserToken
from app.schemas.student import StudentCreate, StudentBase
from app.schemas.recruiter import RecruiterCreate, RecruiterBase
from app.schemas.placement_officer import PlacementOfficerCreate, PlacementOfficerBase
from app.schemas.college import CollegeCreate

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """OAuth2 compatible token login, get an access token for future requests."""
    result = await db.execute(select(User).filter(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token({"sub": user.email, "role": user.role.value})
    refresh_token = create_refresh_token({"sub": user.email, "role": user.role.value})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/login/json", response_model=Token)
async def login_json(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """JSON body login alternative."""
    result = await db.execute(select(User).filter(User.email == user_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
        
    access_token = create_access_token({"sub": user.email, "role": user.role.value})
    refresh_token = create_refresh_token({"sub": user.email, "role": user.role.value})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/register/student", response_model=UserToken, status_code=status.HTTP_201_CREATED)
async def register_student(
    user_data: UserCreate,
    student_data: StudentBase,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create new student user."""
    # Enforce role
    user_data.role = Role.STUDENT
    
    # Check email
    result = await db.execute(select(User).filter(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Check college
    college_result = await db.execute(select(College).filter(College.id == student_data.college_id))
    if not college_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="College not found")
        
    # Create user
    db_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=user_data.role
    )
    db.add(db_user)
    await db.flush() # To get user.id
    
    # Create profile
    db_student = Student(
        user_id=db_user.id,
        first_name=student_data.first_name,
        last_name=student_data.last_name,
        branch=student_data.branch,
        graduation_year=student_data.graduation_year,
        cgpa=student_data.cgpa,
        skills=student_data.skills,
        bio=student_data.bio,
        college_id=student_data.college_id
    )
    db.add(db_student)
    await db.commit()
    
    # Auto-login
    access_token = create_access_token({"sub": db_user.email, "role": db_user.role.value})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "role": db_user.role,
            "profile_id": db_student.id
        }
    }

@router.post("/register/recruiter", response_model=UserToken, status_code=status.HTTP_201_CREATED)
async def register_recruiter(
    user_data: UserCreate,
    recruiter_data: RecruiterBase,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create new recruiter user."""
    user_data.role = Role.RECRUITER
    
    result = await db.execute(select(User).filter(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    db_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=user_data.role
    )
    db.add(db_user)
    await db.flush()
    
    db_recruiter = Recruiter(
        user_id=db_user.id,
        company_name=recruiter_data.company_name,
        email=recruiter_data.email,
        website=recruiter_data.website
    )
    db.add(db_recruiter)
    await db.commit()
    
    access_token = create_access_token({"sub": db_user.email, "role": db_user.role.value})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "role": db_user.role,
            "profile_id": db_recruiter.id
        }
    }

@router.post("/register/placement_officer", response_model=UserToken, status_code=status.HTTP_201_CREATED)
async def register_placement_officer(
    user_data: UserCreate,
    officer_data: PlacementOfficerBase,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create new placement officer user."""
    user_data.role = Role.PLACEMENT_OFFICER
    
    result = await db.execute(select(User).filter(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    db_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
    )
    db.add(db_user)
    await db.flush()
    
    db_officer = PlacementOfficer(
        user_id=db_user.id,
        name=officer_data.name,
        email=officer_data.email,
        designation=officer_data.designation,
        department=officer_data.department,
        college_id=officer_data.college_id
    )
    db.add(db_officer)
    await db.commit()
    
    access_token = create_access_token({"sub": db_user.email, "role": db_user.role.value})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "role": db_user.role,
            "profile_id": db_officer.id
        }
    }
