from enum import Enum
from typing import List, Set
from fastapi import HTTPException, status


class Role(str, Enum):
    """
    User roles in the system.
    
    Multi-tenant hierarchy:
    - STUDENT: Belongs to one college, can apply to college's jobs
    - RECRUITER: Posts jobs for specific colleges
    - PLACEMENT_OFFICER: College admin, manages drives for their college
    - ADMIN: System-wide access
    """
    STUDENT = "student"
    RECRUITER = "recruiter"
    PLACEMENT_OFFICER = "placement_officer"  # NEW
    ADMIN = "admin"


class Permission(str, Enum):
    """Granular permissions for RBAC."""
    # Student permissions
    VIEW_JOBS = "view_jobs"
    APPLY_TO_JOBS = "apply_to_jobs"
    MANAGE_OWN_PROFILE = "manage_own_profile"
    UPLOAD_RESUME = "upload_resume"
    VIEW_OWN_APPLICATIONS = "view_own_applications"
    
    # Recruiter permissions
    POST_JOBS = "post_jobs"
    MANAGE_OWN_JOBS = "manage_own_jobs"
    VIEW_APPLICANTS = "view_applicants"
    RANK_CANDIDATES = "rank_candidates"
    UPDATE_APPLICATION_STATUS = "update_application_status"
    
    # Placement Officer permissions (NEW)
    APPROVE_JOB = "approve_job"                    # Approve job drives
    SET_ELIGIBILITY = "set_eligibility"            # Modify eligibility rules
    VIEW_ALL_STUDENTS = "view_all_students"        # View all students in college
    VIEW_ALL_APPLICATIONS = "view_all_applications"  # View all applications in college
    MANAGE_DRIVES = "manage_drives"                # Manage placement drives
    VIEW_COLLEGE_ANALYTICS = "view_college_analytics"  # View college-level analytics
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    VIEW_ALL_DATA = "view_all_data"
    SYSTEM_SETTINGS = "system_settings"
    MANAGE_COLLEGES = "manage_colleges"  # NEW


# Role to Permissions mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.STUDENT: {
        Permission.VIEW_JOBS,
        Permission.APPLY_TO_JOBS,
        Permission.MANAGE_OWN_PROFILE,
        Permission.UPLOAD_RESUME,
        Permission.VIEW_OWN_APPLICATIONS,
    },
    Role.RECRUITER: {
        Permission.VIEW_JOBS,
        Permission.POST_JOBS,
        Permission.MANAGE_OWN_JOBS,
        Permission.VIEW_APPLICANTS,
        Permission.RANK_CANDIDATES,
        Permission.UPDATE_APPLICATION_STATUS,
    },
    Role.PLACEMENT_OFFICER: {
        # Can do everything recruiters can do
        Permission.VIEW_JOBS,
        Permission.VIEW_APPLICANTS,
        Permission.RANK_CANDIDATES,
        Permission.UPDATE_APPLICATION_STATUS,
        # Plus college-specific admin powers
        Permission.APPROVE_JOB,
        Permission.SET_ELIGIBILITY,
        Permission.VIEW_ALL_STUDENTS,
        Permission.VIEW_ALL_APPLICATIONS,
        Permission.MANAGE_DRIVES,
        Permission.VIEW_COLLEGE_ANALYTICS,
    },
    Role.ADMIN: set(Permission),  # Admin has all permissions
}


def has_permission(user_role: Role, required_permission: Permission) -> bool:
    """
    Check if a role has a specific permission.
    
    Args:
        user_role: The role to check
        required_permission: The permission required
        
    Returns:
        True if role has permission, False otherwise
    """
    return required_permission in ROLE_PERMISSIONS.get(user_role, set())


def require_permission(required_permission: Permission):
    """
    Decorator to enforce permission-based access control.
    
    Args:
        required_permission: The permission required to access the endpoint
        
    Returns:
        Decorator function
    """
    def permission_checker(user_role: Role) -> bool:
        if not has_permission(user_role, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required permission: {required_permission.value}"
            )
        return True
    
    return permission_checker


def check_role(user_role: Role, allowed_roles: List[Role]) -> bool:
    """
    Check if user's role is in the list of allowed roles.
    
    Args:
        user_role: User's current role
        allowed_roles: List of roles that are allowed
        
    Returns:
        True if role is allowed
        
    Raises:
        HTTPException: If role is not allowed
    """
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
        )
    return True
