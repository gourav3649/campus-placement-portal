from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.config import get_settings
from app.core.security import decode_token
from app.core.rbac import Role
from app.models.user import User
from app.models.student import Student
from app.models.recruiter import Recruiter
from app.models.placement_officer import PlacementOfficer

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
        
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception
        
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Role-specific dependencies
async def get_current_student(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Student:
    if current_user.role != Role.STUDENT:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    result = await db.execute(select(Student).filter(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return student


async def get_current_recruiter(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Recruiter:
    if current_user.role != Role.RECRUITER:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    result = await db.execute(select(Recruiter).filter(Recruiter.user_id == current_user.id))
    recruiter = result.scalar_one_or_none()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter profile not found")
    return recruiter


async def get_current_placement_officer(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> PlacementOfficer:
    if current_user.role != Role.PLACEMENT_OFFICER:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    result = await db.execute(select(PlacementOfficer).filter(PlacementOfficer.user_id == current_user.id))
    officer = result.scalar_one_or_none()
    if not officer:
        raise HTTPException(status_code=404, detail="Placement officer profile not found")
    return officer


def get_current_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user
