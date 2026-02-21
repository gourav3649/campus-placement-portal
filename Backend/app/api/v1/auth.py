from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.core.rbac import Role
from app.core.config import get_settings
from app.models.user import User
from app.models.student import Student
from app.models.recruiter import Recruiter
from app.schemas.user import UserCreate, Token, LoginRequest, User as UserSchema
from app.schemas.student import StudentCreate
from app.schemas.recruiter import RecruiterCreate

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register/student", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register_student(
    user_data: UserCreate,
    student_data: StudentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new student user.
    
    Creates both user account and student profile.
    SINGLE-COLLEGE MODE: college_id auto-injected from settings.
    """
    settings = get_settings()
    
    # SINGLE-COLLEGE MODE: Auto-inject college_id from settings
    college_id = settings.COLLEGE_ID
    
    # Validate college exists
    from app.models.college import College
    college_result = await db.execute(
        select(College).filter(College.id == college_id, College.is_active == True)
    )
    college = college_result.scalar_one_or_none()
    if not college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="College not found or inactive. Please check COLLEGE_ID in settings."
        )
    
    # Check if email already exists
    result = await db.execute(select(User).filter(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role=Role.STUDENT
    )
    db.add(user)
    await db.flush()  # Flush to get user.id
    
    # Create student profile with college assignment
    student = Student(
        user_id=user.id,
        college_id=college_id,  # SINGLE-COLLEGE MODE: Auto-injected from settings
        first_name=student_data.first_name,
        last_name=student_data.last_name,
        phone=student_data.phone,
        enrollment_number=student_data.enrollment_number,
        university=student_data.university,
        degree=student_data.degree,
        major=student_data.major,
        graduation_year=student_data.graduation_year,
        cgpa=student_data.cgpa,
        branch=student_data.branch if hasattr(student_data, 'branch') else None,
        has_backlogs=student_data.has_backlogs if hasattr(student_data, 'has_backlogs') else False,
        is_placed=False,  # Default: not placed yet
        bio=student_data.bio,
        linkedin_url=str(student_data.linkedin_url) if student_data.linkedin_url else None,
        github_url=str(student_data.github_url) if student_data.github_url else None,
        portfolio_url=str(student_data.portfolio_url) if student_data.portfolio_url else None,
        skills=student_data.skills
    )
    db.add(student)
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/register/recruiter", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register_recruiter(
    user_data: UserCreate,
    recruiter_data: RecruiterCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new recruiter user.
    
    Creates both user account and recruiter profile.
    """
    # Check if email already exists
    result = await db.execute(select(User).filter(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role=Role.RECRUITER
    )
    db.add(user)
    await db.flush()
    
    # Create recruiter profile
    recruiter = Recruiter(
        user_id=user.id,
        company_name=recruiter_data.company_name,
        company_website=str(recruiter_data.company_website) if recruiter_data.company_website else None,
        company_description=recruiter_data.company_description,
        first_name=recruiter_data.first_name,
        last_name=recruiter_data.last_name,
        position=recruiter_data.position,
        phone=recruiter_data.phone,
        linkedin_url=str(recruiter_data.linkedin_url) if recruiter_data.linkedin_url else None
    )
    db.add(recruiter)
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint using OAuth2 password flow.
    
    Returns access and refresh tokens.
    """
    # Get user by email
    result = await db.execute(select(User).filter(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create tokens
    token_data = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/login/json", response_model=Token)
async def login_json(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint with JSON body.
    
    Alternative to OAuth2 password flow for easier testing.
    """
    # Get user by email
    result = await db.execute(select(User).filter(User.email == credentials.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create tokens
    token_data = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
