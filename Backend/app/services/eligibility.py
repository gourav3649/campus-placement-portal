"""
Eligibility service: checks a student against a job's requirements.
Returns (is_eligible, list_of_reasons).
"""
from typing import Tuple, List
from app.models.student import Student
from app.models.job import Job


def check_eligibility(student: Student, job: Job) -> Tuple[bool, List[str]]:
    failures: List[str] = []

    # 1. CGPA check
    if job.min_cgpa is not None and student.cgpa < job.min_cgpa:
        failures.append(
            f"CGPA {student.cgpa:.2f} is below the minimum required {job.min_cgpa:.2f}"
        )

    # 2. Branch check
    if job.allowed_branches:
        if student.branch not in job.allowed_branches:
            failures.append(
                f"Branch '{student.branch}' is not in the allowed branches: {', '.join(job.allowed_branches)}"
            )

    # 3. Backlogs check
    if job.max_backlogs is not None:
        # If max_backlogs is 0, students with any backlog are excluded
        if student.has_backlogs and job.max_backlogs == 0:
            failures.append("Students with active backlogs are not eligible for this drive")

    # 4. Already placed check
    if job.exclude_placed_students and student.is_placed:
        failures.append("Already placed students are not eligible for this drive")

    return (len(failures) == 0, failures)
