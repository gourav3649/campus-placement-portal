"""
Eligibility Rules Engine

Evaluates student eligibility for job applications based on college-defined rules.
This is a CRITICAL pre-filter BEFORE AI ranking to ensure:
1. Only qualified students are ranked
2. AI resources are not wasted on ineligible candidates
3. College policies are enforced

Eligibility Rules:
1. College Match: student.college_id == job.college_id
2. CGPA: student.cgpa >= job.min_cgpa (if defined)
3. Branch: student.branch in job.allowed_branches (if defined)
4. Backlogs: student.has_backlogs <= job.max_backlogs (if defined)
5. Placement Status: student.is_placed == False (if job.exclude_placed_students)
"""

import json
from typing import Dict, List, Tuple, Optional
from app.models.student import Student
from app.models.job import Job


class EligibilityRule:
    """Base class for eligibility rules."""
    
    def __init__(self, rule_name: str, required: bool = True):
        """
        Initialize rule.
        
        Args:
            rule_name: Human-readable name of the rule
            required: If True, failure blocks application
        """
        self.rule_name = rule_name
        self.required = required
    
    def evaluate(self, student: Student, job: Job) -> Tuple[bool, Optional[str]]:
        """
        Evaluate rule.
        
        Args:
            student: Student applying
            job: Job being applied to
            
        Returns:
            (is_eligible, failure_reason)
        """
        raise NotImplementedError


class CollegeMatchRule(EligibilityRule):
    """Student must belong to the job's target college."""
    
    def __init__(self):
        super().__init__("College Match", required=True)
    
    def evaluate(self, student: Student, job: Job) -> Tuple[bool, Optional[str]]:
        """Check if student belongs to job's college."""
        if student.college_id != job.college_id:
            return False, f"college_mismatch"
        return True, None


class CGPARule(EligibilityRule):
    """Student's CGPA must meet minimum requirement."""
    
    def __init__(self):
        super().__init__("Minimum CGPA", required=False)
    
    def evaluate(self, student: Student, job: Job) -> Tuple[bool, Optional[str]]:
        """Check if student meets CGPA requirement."""
        # If job doesn't set min_cgpa, auto-pass
        if job.min_cgpa is None:
            return True, None
        
        # If student doesn't have CGPA, fail
        if student.cgpa is None:
            return False, f"cgpa_not_available"
        
        # Check CGPA threshold
        if student.cgpa < job.min_cgpa:
            return False, f"min_cgpa_not_met (required: {job.min_cgpa}, has: {student.cgpa})"
        
        return True, None


class BranchRule(EligibilityRule):
    """Student's branch must be in allowed list."""
    
    def __init__(self):
        super().__init__("Allowed Branches", required=False)
    
    def evaluate(self, student: Student, job: Job) -> Tuple[bool, Optional[str]]:
        """Check if student's branch is allowed."""
        # If job doesn't specify branches, auto-pass
        if not job.allowed_branches:
            return True, None
        
        # Parse allowed branches (stored as JSON)
        try:
            allowed_branches = json.loads(job.allowed_branches)
        except (json.JSONDecodeError, TypeError):
            # If invalid JSON, treat as auto-pass
            return True, None
        
        # If student doesn't have branch, fail
        if not student.branch:
            return False, f"branch_not_specified"
        
        # Check if student's branch is in allowed list
        if student.branch not in allowed_branches:
            return False, f"branch_not_allowed (allowed: {', '.join(allowed_branches)})"
        
        return True, None


class BacklogRule(EligibilityRule):
    """Student's backlogs must not exceed maximum."""
    
    def __init__(self):
        super().__init__("Maximum Backlogs", required=False)
    
    def evaluate(self, student: Student, job: Job) -> Tuple[bool, Optional[str]]:
        """Check if student's backlogs are within limit."""
        # If job doesn't set max_backlogs, auto-pass
        if job.max_backlogs is None:
            return True, None
        
        # If student has backlogs but job allows 0, fail
        if job.max_backlogs == 0 and student.has_backlogs:
            return False, f"no_backlogs_allowed"
        
        # Note: has_backlogs is a boolean, not a count
        # For now, if has_backlogs=True and max_backlogs=0, fail
        # In future, add backlog_count field to Student model
        if student.has_backlogs and job.max_backlogs == 0:
            return False, f"backlogs_present"
        
        return True, None


class PlacementStatusRule(EligibilityRule):
    """Student must not be already placed (if job excludes placed students)."""
    
    def __init__(self):
        super().__init__("Not Already Placed", required=False)
    
    def evaluate(self, student: Student, job: Job) -> Tuple[bool, Optional[str]]:
        """Check if student is already placed."""
        # If job allows placed students, auto-pass
        if not job.exclude_placed_students:
            return True, None
        
        # If student is already placed, fail
        if student.is_placed:
            return False, f"already_placed"
        
        return True, None


class EligibilityEngine:
    """
    Main engine to evaluate all eligibility rules.
    
    Usage:
        engine = EligibilityEngine()
        is_eligible, reasons = engine.check_eligibility(student, job)
    """
    
    def __init__(self):
        """Initialize with all eligibility rules."""
        self.rules: List[EligibilityRule] = [
            CollegeMatchRule(),      # CRITICAL: Multi-tenancy enforcement
            CGPARule(),              # Academic performance
            BranchRule(),            # Department/stream filter
            BacklogRule(),           # Academic standing
            PlacementStatusRule(),   # One student, one placement
        ]
    
    def check_eligibility(
        self, 
        student: Student, 
        job: Job
    ) -> Tuple[bool, List[str]]:
        """
        Check if student is eligible for job.
        
        Args:
            student: Student applying
            job: Job being applied to
            
        Returns:
            (is_eligible, failure_reasons)
            
        Example:
            >>> engine = EligibilityEngine()
            >>> is_eligible, reasons = engine.check_eligibility(student, job)
            >>> if not is_eligible:
            >>>     print(f"Ineligible: {', '.join(reasons)}")
        """
        failure_reasons = []
        
        for rule in self.rules:
            is_eligible, reason = rule.evaluate(student, job)
            
            if not is_eligible:
                if rule.required:
                    # Critical rule failed - immediately return False
                    return False, [reason] if reason else ["eligibility_check_failed"]
                else:
                    # Optional rule failed - collect reason
                    if reason:
                        failure_reasons.append(reason)
        
        # If any failure reasons accumulated, student is ineligible
        if failure_reasons:
            return False, failure_reasons
        
        # All rules passed
        return True, []
    
    def get_eligibility_summary(
        self,
        student: Student,
        job: Job
    ) -> Dict[str, any]:
        """
        Get detailed eligibility summary for debugging.
        
        Returns:
            Dictionary with rule-by-rule results
        """
        summary = {
            "student_id": student.id,
            "job_id": job.id,
            "is_eligible": None,
            "rules": []
        }
        
        for rule in self.rules:
            is_eligible, reason = rule.evaluate(student, job)
            summary["rules"].append({
                "rule_name": rule.rule_name,
                "passed": is_eligible,
                "failure_reason": reason,
                "required": rule.required
            })
        
        # Overall eligibility
        is_eligible, reasons = self.check_eligibility(student, job)
        summary["is_eligible"] = is_eligible
        summary["failure_reasons"] = reasons
        
        return summary
