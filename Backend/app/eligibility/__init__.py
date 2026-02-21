"""
Eligibility Module

Pre-AI filtering engine that enforces college-defined eligibility rules.

Critical for multi-tenant architecture:
- Ensures students only apply to their college's jobs
- Filters ineligible candidates BEFORE expensive AI ranking
- Enforces academic and placement policies

Typical workflow:
1. Student submits application
2. EligibilityService.check_application_eligibility() runs
3. If eligible → status = PENDING → queued for AI ranking
4. If ineligible → status = ELIGIBILITY_FAILED → NOT sent to AI

Usage:
    from app.eligibility import EligibilityService
    
    service = EligibilityService()
    is_eligible, reasons = await service.check_application_eligibility(db, application)
"""

from app.eligibility.rules_engine import (
    EligibilityEngine,
    EligibilityRule,
    CollegeMatchRule,
    CGPARule,
    BranchRule,
    BacklogRule,
    PlacementStatusRule,
)
from app.eligibility.eligibility_service import EligibilityService

__all__ = [
    "EligibilityEngine",
    "EligibilityRule",
    "CollegeMatchRule",
    "CGPARule",
    "BranchRule",
    "BacklogRule",
    "PlacementStatusRule",
    "EligibilityService",
]
