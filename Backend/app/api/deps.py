from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.security import decode_token
from app.core.rbac import Role, Permission, check_role, require_permission
from app.models.user import User
from app.models.student import Student
from app.models.recruiter import Recruiter
from app.models.placement_officer import PlacementOfficer  # NEW

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        token: JWT access token
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Decode token
    payload = decode_token(token)
    user_id_str = payload.get("sub")
    
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token"
        )
    
    # Get user from database
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_student(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Student:
    """
    Get current student profile.
    
    Requires user to have STUDENT role.
    """
    check_role(current_user.role, [Role.STUDENT])
    
    result = await db.execute(
        select(Student).filter(Student.user_id == current_user.id)
    )
    student = result.scalar_one_or_none()
    
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    return student


async def get_current_recruiter(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Recruiter:
    """
    Get current recruiter profile.
    
    Requires user to have RECRUITER role.
    """
    check_role(current_user.role, [Role.RECRUITER])
    
    result = await db.execute(
        select(Recruiter).filter(Recruiter.user_id == current_user.id)
    )
    recruiter = result.scalar_one_or_none()
    
    if recruiter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recruiter profile not found"
        )
    
    return recruiter


async def get_current_placement_officer(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> PlacementOfficer:
    """
    Get current placement officer profile.
    
    Requires user to have PLACEMENT_OFFICER role.
    Multi-tenant: Officer has access only to their college's data.
    """
    check_role(current_user.role, [Role.PLACEMENT_OFFICER])
    
    result = await db.execute(
        select(PlacementOfficer).filter(PlacementOfficer.user_id == current_user.id)
    )
    officer = result.scalar_one_or_none()
    
    if officer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Placement officer profile not found"
        )
    
    return officer


def require_role(*allowed_roles: Role):
    """
    Dependency to require specific roles.
    
    Usage:
        @router.get("/endpoint", dependencies=[Depends(require_role(Role.STUDENT))])
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        check_role(current_user.role, list(allowed_roles))
        return current_user
    
    return role_checker


def require_permissions(*permissions: Permission):
    """
    Dependency to require specific permissions.
    
    Usage:
        @router.post("/jobs", dependencies=[Depends(require_permissions(Permission.POST_JOBS))])
    """
    async def permission_checker(current_user: User = Depends(get_current_active_user)):
        for permission in permissions:
            require_permission(permission)(current_user.role)
        return current_user
    
    return permission_checker
