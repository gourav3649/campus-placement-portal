# Eligibility Revalidation and Defensive Enforcement

## Overview

This document details the implementation of **defensive eligibility revalidation** to prevent stale eligibility data from affecting AI ranking and application processing.

---

## Problem: Stale Eligibility Data

### Scenarios Where Eligibility Can Become Stale

1. **Job eligibility rules updated** after applications submitted
   - Recruiter changes `min_cgpa` from 7.0 to 8.0
   - Recruiter adds `exclude_placed_students = True`
   - Recruiter updates `allowed_branches` list

2. **Student data changes** after application submitted
   - Student gets placed → `is_placed = True`
   - Student's CGPA updated (grade improvement or correction)
   - Student's backlog status changes

3. **Time gap** between eligibility check and AI ranking
   - Application submitted Monday, marked eligible
   - Student gets placed Tuesday
   - AI ranking runs Wednesday with stale eligibility

### Risk Without Revalidation

- **Inaccurate rankings**: Placed students ranked for jobs excluding placed students
- **Wasted AI resources**: Scoring applications that shouldn't be processed
- **Compliance violations**: Students with CGPA 7.5 ranked for jobs requiring 8.0
- **Unfair comparisons**: Ranking pool includes ineligible candidates

---

## Solution: Multi-Layer Revalidation

### 1. Defensive Revalidation in Ranking Orchestrator

**File**: `app/matching/ranking_orchestrator.py`

**When**: Every time an application is about to be scored

**Logic**: Before generating embeddings and AI scoring, recheck eligibility

```python
async def rank_applications(
    self,
    db: AsyncSession,
    job_id: int,
    rerank: bool = False
) -> Dict[str, Any]:
    """
    Rank all applications for a job.
    
    **Optimization: Job embedding computed ONCE, reused for all candidates.**
    **Security: Only ranks APPROVED drives with ELIGIBLE applications.**
    **Defensive: Revalidates eligibility before scoring each application.**
    
    Args:
        db: Database session
        job_id: Job ID to rank applications for
        rerank: Whether to recalculate scores for already-scored applications
        
    Returns:
        Dictionary with ranking statistics including revalidation stats
    """
    # Step 1: Fetch job
    job_result = await db.execute(select(Job).filter(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise ValueError(f"Job {job_id} not found")
    
    # SECURITY: Prevent ranking if drive not approved
    from app.models.job import DriveStatus
    if hasattr(job, 'drive_status') and job.drive_status != DriveStatus.APPROVED:
        return {
            "job_id": job_id,
            "applications_ranked": 0,
            "message": f"Cannot rank applications: Drive status is {job.drive_status}. Must be APPROVED.",
            "error": "drive_not_approved"
        }
    
    # Step 2: Extract job features (COMPUTE EMBEDDING ONCE)
    print(f"[Orchestrator] Extracting job features for job {job_id}...")
    job_features = self.feature_extractor.extract_job_features(job)
    print(f"[Orchestrator] Job embedding computed (will be reused for all candidates)")
    
    # Step 3: FILTER ELIGIBLE APPLICATIONS
    print(f"[Orchestrator] Filtering eligible applications...")
    eligible_applications = await self.eligibility_service.filter_eligible_applications(
        db=db,
        job_id=job_id,
        check_all=rerank
    )
    
    print(f"[Orchestrator] Found {len(eligible_applications)} eligible applications")
    
    if not eligible_applications:
        stats = await self.eligibility_service.get_eligibility_stats(db, job_id)
        return {
            "job_id": job_id,
            "applications_ranked": 0,
            "eligible_count": 0,
            "ineligible_count": stats.get("ineligible_count", 0),
            "rejection_reasons": stats.get("rejection_reasons", {}),
            "message": "No eligible applications to rank"
        }
    
    # ===== Step 4: Process with DEFENSIVE REVALIDATION =====
    applications = eligible_applications
    scored_count = 0
    skipped_count = 0  # Track applications that became ineligible during revalidation
    
    for application in applications:
        try:
            # Fetch student
            student_result = await db.execute(
                select(Student).filter(Student.id == application.student_id)
            )
            student = student_result.scalar_one()
            
            # ===== DEFENSIVE REVALIDATION =====
            # CRITICAL: Check eligibility again right before scoring
            # This catches stale eligibility from:
            # - Job rules updated after initial eligibility check
            # - Student placement status changed
            # - Student data updated (CGPA, backlogs, etc.)
            
            print(f"[Orchestrator] Revalidating eligibility for application {application.id}...")
            is_still_eligible, failure_reasons = await self.eligibility_service.check_application_eligibility(
                db=db,
                application=application,
                update_db=True  # Update database if eligibility changed
            )
            
            if not is_still_eligible:
                # Application became ineligible between initial check and ranking
                print(f"[Orchestrator] Application {application.id} became ineligible: {', '.join(failure_reasons)}")
                skipped_count += 1
                continue  # Skip scoring - don't waste AI resources
            
            # Proceed with scoring only if STILL eligible
            # ... (existing AI scoring logic)
            
            # Fetch resume (optional)
            resume = None
            if application.resume_id:
                resume_result = await db.execute(
                    select(Resume).filter(Resume.id == application.resume_id)
                )
                resume = resume_result.scalar_one_or_none()
            
            # Extract candidate features
            candidate_features = self.feature_extractor.extract_candidate_features(
                application_id=application.id,
                student=student,
                resume=resume,
                compute_embedding=True
            )
            
            # Score candidate (using PRECOMPUTED job embedding)
            score_breakdown = self.scoring_engine.score_candidate(
                job_features=job_features,
                candidate_features=candidate_features
            )
            
            # Generate AI summary
            ai_summary = self._generate_ai_summary(
                job_title=job.title,
                candidate_name=candidate_features.name,
                candidate_cgpa=candidate_features.cgpa,
                candidate_university=candidate_features.university,
                score_breakdown=score_breakdown
            )
            
            # Update application with scores
            application.match_score = score_breakdown.overall_score
            application.skills_match_score = score_breakdown.skills_score
            application.experience_match_score = score_breakdown.experience_score
            application.ai_summary = ai_summary["summary"]
            application.strengths = json.dumps(ai_summary["strengths"])
            application.weaknesses = json.dumps(ai_summary["weaknesses"])
            
            scored_count += 1
            
        except Exception as e:
            print(f"[Orchestrator] Error scoring application {application.id}: {str(e)}")
            continue
    
    # Commit all scores
    await db.commit()
    print(f"[Orchestrator] Scored {scored_count} eligible applications, skipped {skipped_count} that became ineligible")
    
    # Step 5: Assign ranks (only among currently eligible)
    ranked_result = await db.execute(
        select(Application)
        .filter(Application.job_id == job_id)
        .filter(Application.is_eligible == True)
        .filter(Application.match_score.isnot(None))
        .order_by(Application.match_score.desc())
    )
    ranked_applications = ranked_result.scalars().all()
    
    for rank, app in enumerate(ranked_applications, start=1):
        app.rank = rank
        app.rank_among_eligible = rank
    
    await db.commit()
    
    # Step 6: Get final stats
    eligibility_stats = await self.eligibility_service.get_eligibility_stats(db, job_id)
    
    return {
        "job_id": job_id,
        "applications_ranked": scored_count,
        "applications_skipped_during_revalidation": skipped_count,  # NEW
        "total_ranked_applications": len(ranked_applications),
        "eligible_count": eligibility_stats.get("eligible_count", 0),
        "ineligible_count": eligibility_stats.get("ineligible_count", 0),
        "not_checked_count": eligibility_stats.get("not_checked_count", 0),
        "rejection_reasons": eligibility_stats.get("rejection_reasons", {}),
        "message": "Ranking completed successfully with defensive revalidation"
    }
```

**Key Changes**:
- Added `skipped_count` variable to track applications that became ineligible during revalidation
- **Before each AI scoring**: Call `check_application_eligibility()` to revalidate
- **If ineligible**: Skip scoring, increment `skipped_count`, continue to next application
- **Returns**: `applications_skipped_during_revalidation` stat to show stale eligibility detection

---

### 2. Revalidate All Applications Method

**File**: `app/eligibility/eligibility_service.py`

**New Method**: `revalidate_all_applications()`

**Purpose**: Recheck eligibility for ALL applications (both currently eligible and ineligible)

```python
async def revalidate_all_applications(
    self,
    db: AsyncSession,
    job_id: int
) -> Dict[str, int]:
    """
    Revalidate eligibility for ALL applications (both eligible and ineligible).
    
    Use cases:
    1. Job eligibility rules updated (min_cgpa, allowed_branches, etc.)
    2. Defensive check before ranking
    3. Manual revalidation triggered by placement officer
    
    This differs from mark_ineligible_applications which only checks PENDING apps.
    This method rechecks ALL applications to catch:
    - Previously eligible apps that became ineligible (e.g., student got placed)
    - Previously ineligible apps that became eligible (e.g., rules loosened)
    
    Args:
        db: Database session
        job_id: Job ID
        
    Returns:
        Dictionary with revalidation statistics
    """
    # Fetch ALL applications for this job (regardless of status)
    query = select(Application).filter(Application.job_id == job_id)
    result = await db.execute(query)
    applications = result.scalars().all()
    
    stats = {
        "total_applications": len(applications),
        "newly_eligible": 0,        # Was ineligible, now eligible
        "newly_ineligible": 0,      # Was eligible, now ineligible
        "still_eligible": 0,
        "still_ineligible": 0,
        "eligibility_changes": []   # Detailed change log
    }
    
    for app in applications:
        old_eligibility = app.is_eligible
        
        # Recheck eligibility
        is_eligible, reasons = await self.check_application_eligibility(
            db, app, update_db=True
        )
        
        # Track changes
        if old_eligibility is None:
            # First time checked
            if is_eligible:
                stats["newly_eligible"] += 1
            else:
                stats["newly_ineligible"] += 1
        elif old_eligibility == True and is_eligible == False:
            # Became ineligible
            stats["newly_ineligible"] += 1
            stats["eligibility_changes"].append({
                "application_id": app.id,
                "student_id": app.student_id,
                "change": "eligible_to_ineligible",
                "reasons": reasons
            })
            logger.warning(
                f"Application {app.id} became INELIGIBLE: {', '.join(reasons)}"
            )
        elif old_eligibility == False and is_eligible == True:
            # Became eligible
            stats["newly_eligible"] += 1
            stats["eligibility_changes"].append({
                "application_id": app.id,
                "student_id": app.student_id,
                "change": "ineligible_to_eligible",
                "reasons": []
            })
            logger.info(
                f"Application {app.id} became ELIGIBLE (rules may have changed)"
            )
        elif is_eligible:
            stats["still_eligible"] += 1
        else:
            stats["still_ineligible"] += 1
    
    logger.info(
        f"Revalidated {stats['total_applications']} applications for job {job_id}: "
        f"{stats['newly_ineligible']} became ineligible, {stats['newly_eligible']} became eligible"
    )
    
    return stats
```

**Key Features**:
- Rechecks **ALL** applications (not just PENDING)
- Tracks **bidirectional changes**: eligible→ineligible AND ineligible→eligible
- Returns detailed stats with `eligibility_changes` array
- Logs warnings for eligibility downgrades

---

### 3. Manual Revalidation Endpoint

**File**: `app/api/v1/jobs.py`

**New Endpoint**: `POST /jobs/{job_id}/revalidate-eligibility`

**Purpose**: Allow manual triggering of eligibility revalidation

```python
@router.post("/{job_id}/revalidate-eligibility")
async def revalidate_job_eligibility(
    job_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revalidate eligibility for all applications to this job.
    
    Triggers a complete recheck of all applications, catching:
    - Students who got placed (if job excludes placed students)
    - Students whose CGPA/backlogs changed
    - Applications that became eligible after rule changes
    
    Accessible to:
    - Recruiters (who own the job)
    - Placement Officers (for their college's jobs)
    - Admins
    
    Returns:
        Revalidation statistics showing eligibility changes
    """
    from app.eligibility import EligibilityService
    from app.core.rbac import Role
    
    # Fetch job
    result = await db.execute(select(Job).filter(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Authorization check
    if current_user.role == Role.RECRUITER:
        from app.models.recruiter import Recruiter
        recruiter_result = await db.execute(
            select(Recruiter).filter(Recruiter.user_id == current_user.id)
        )
        recruiter = recruiter_result.scalar_one_or_none()
        
        if not recruiter or job.recruiter_id != recruiter.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to revalidate this job's applications"
            )
    
    elif current_user.role == Role.PLACEMENT_OFFICER:
        from app.models.placement_officer import PlacementOfficer
        officer_result = await db.execute(
            select(PlacementOfficer).filter(PlacementOfficer.user_id == current_user.id)
        )
        officer = officer_result.scalar_one_or_none()
        
        # Multi-tenant check: officer can only revalidate jobs for their college
        if not officer or (hasattr(job, 'college_id') and job.college_id != officer.college_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to revalidate this job's applications"
            )
    
    elif current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to revalidate eligibility"
        )
    
    # Trigger revalidation
    eligibility_service = EligibilityService()
    stats = await eligibility_service.revalidate_all_applications(db, job_id)
    
    return {
        "job_id": job_id,
        "job_title": job.title,
        "revalidation_stats": stats,
        "message": f"Revalidated {stats['total_applications']} applications. "
                   f"{stats['newly_ineligible']} became ineligible, "
                   f"{stats['newly_eligible']} became eligible."
    }
```

**Authorization**:
- **Recruiters**: Can revalidate jobs they own
- **Placement Officers**: Can revalidate jobs from their college (multi-tenant check)
- **Admins**: Can revalidate any job

**Example Response**:
```json
{
  "job_id": 42,
  "job_title": "Software Engineer - Google",
  "revalidation_stats": {
    "total_applications": 120,
    "newly_eligible": 5,
    "newly_ineligible": 12,
    "still_eligible": 68,
    "still_ineligible": 35,
    "eligibility_changes": [
      {
        "application_id": 501,
        "student_id": 201,
        "change": "eligible_to_ineligible",
        "reasons": ["already_placed"]
      },
      {
        "application_id": 502,
        "student_id": 203,
        "change": "eligible_to_ineligible",
        "reasons": ["cgpa_below_threshold"]
      }
    ]
  },
  "message": "Revalidated 120 applications. 12 became ineligible, 5 became eligible."
}
```

---

### 4. Automatic Revalidation on Job Update

**File**: `app/api/v1/jobs.py`

**Endpoint**: `PUT /jobs/{job_id}`

**Trigger**: When eligibility rules are updated

**Updated Logic**:

```python
@router.put("/{job_id}", response_model=JobSchema)
async def update_job(
    job_id: int,
    job_update: JobUpdate,
    current_recruiter: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a job posting.
    
    Requires: RECRUITER role, must own the job
    
    AUTOMATIC REVALIDATION: If eligibility rules change, all applications are rechecked.
    """
    result = await db.execute(select(Job).filter(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check ownership
    if job.recruiter_id != current_recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this job"
        )
    
    # ===== Check if eligibility rules are being updated =====
    eligibility_fields = {'min_cgpa', 'allowed_branches', 'max_backlogs', 'exclude_placed_students'}
    update_data = job_update.model_dump(exclude_unset=True)
    eligibility_changed = bool(eligibility_fields & set(update_data.keys()))
    
    # Update fields
    for field, value in update_data.items():
        setattr(job, field, value)
    
    await db.commit()
    await db.refresh(job)
    
    # ===== TRIGGER ELIGIBILITY REVALIDATION if rules changed =====
    if eligibility_changed:
        from app.eligibility import EligibilityService
        eligibility_service = EligibilityService()
        
        print(f"[Jobs] Eligibility rules updated for job {job_id}, triggering revalidation...")
        revalidation_stats = await eligibility_service.revalidate_all_applications(db, job_id)
        print(f"[Jobs] Revalidation complete: {revalidation_stats['newly_ineligible']} became ineligible, "
              f"{revalidation_stats['newly_eligible']} became eligible")
    
    return job
```

**Eligibility Fields Monitored**:
- `min_cgpa` - Minimum CGPA requirement
- `allowed_branches` - List of allowed branches
- `max_backlogs` - Maximum backlogs allowed
- `exclude_placed_students` - Whether to exclude already-placed students

**Example Scenarios**:

**Scenario 1**: Recruiter raises CGPA bar
```bash
PUT /api/v1/jobs/42
{
  "min_cgpa": 8.5  # Was 7.5
}

# Automatic revalidation triggered
# Students with CGPA 7.5-8.4 marked ineligible
```

**Scenario 2**: Recruiter adds placement exclusion
```bash
PUT /api/v1/jobs/42
{
  "exclude_placed_students": true  # Was false
}

# Automatic revalidation triggered
# All placed students' applications marked ineligible
```

---

### 5. Automatic Revalidation on Student Update

**File**: `app/api/v1/students.py`

**Endpoint**: `PUT /students/me`

**Trigger**: When placement status changes

**Updated Logic**:

```python
@router.put("/me", response_model=StudentProfile)
async def update_my_profile(
    profile_update: StudentUpdate,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current student's profile.
    
    Requires: STUDENT role
    
    AUTOMATIC REVALIDATION: If placement status changes, all applications are rechecked.
    """
    # ===== Check if placement status is changing =====
    placement_status_changed = False
    if 'is_placed' in profile_update.model_dump(exclude_unset=True):
        old_is_placed = current_student.is_placed
        new_is_placed = profile_update.is_placed
        if old_is_placed != new_is_placed:
            placement_status_changed = True
            print(f"[Students] Student {current_student.id} placement status changing: {old_is_placed} -> {new_is_placed}")
    
    # Update only provided fields
    update_data = profile_update.model_dump(exclude_unset=True)
    
    # Convert URLs to strings
    for url_field in ['linkedin_url', 'github_url', 'portfolio_url']:
        if url_field in update_data and update_data[url_field] is not None:
            update_data[url_field] = str(update_data[url_field])
    
    for field, value in update_data.items():
        setattr(current_student, field, value)
    
    await db.commit()
    await db.refresh(current_student)
    
    # ===== TRIGGER ELIGIBILITY REVALIDATION if placement status changed =====
    if placement_status_changed:
        from app.eligibility import EligibilityService
        from app.models.application import Application
        eligibility_service = EligibilityService()
        
        # Get all jobs this student applied to
        apps_result = await db.execute(
            select(Application).filter(Application.student_id == current_student.id)
        )
        applications = apps_result.scalars().all()
        
        if applications:
            print(f"[Students] Revalidating eligibility for {len(applications)} applications...")
            revalidated_count = 0
            for app in applications:
                is_eligible, reasons = await eligibility_service.check_application_eligibility(
                    db, app, update_db=True
                )
                revalidated_count += 1
            print(f"[Students] Revalidated {revalidated_count} applications for student {current_student.id}")
    
    # ... (rest of endpoint returns StudentProfile)
```

**Example Scenarios**:

**Scenario 1**: Student gets placed
```bash
PUT /api/v1/students/me
{
  "is_placed": true  # Was false
}

# Automatic revalidation triggered
# All applications to jobs with exclude_placed_students=true become ineligible
```

**Scenario 2**: Placement status corrected
```bash
PUT /api/v1/students/me
{
  "is_placed": false  # Was incorrectly set to true
}

# Automatic revalidation triggered
# Applications may become eligible again
```

---

## Revalidation Workflow Summary

### 1. On Application Submission
```
Student submits application
    ↓
Initial eligibility check
    ↓
Mark as eligible/ineligible
    ↓
Store eligibility_checked_at timestamp
```

### 2. On Job Eligibility Rule Update
```
Recruiter updates min_cgpa/branches/etc.
    ↓
Detect eligibility field change
    ↓
Call revalidate_all_applications()
    ↓
All applications rechecked
    ↓
Update is_eligible, eligibility_reasons
    ↓
Log eligibility changes
```

### 3. On Student Placement Status Change
```
Student/admin updates is_placed
    ↓
Detect placement status change
    ↓
Fetch all applications by student
    ↓
Revalidate each application
    ↓
Mark ineligible if job excludes placed students
```

### 4. Before AI Ranking (Defensive)
```
Ranking orchestrator starts
    ↓
Fetch eligible applications
    ↓
For each application:
    ├─ REVALIDATE eligibility before scoring
    ├─ If now ineligible: skip, increment skipped_count
    └─ If still eligible: proceed with AI scoring
    ↓
Return ranking with skipped_count stat
```

### 5. Manual Revalidation (On Demand)
```
POST /jobs/{job_id}/revalidate-eligibility
    ↓
Call revalidate_all_applications()
    ↓
Return detailed stats with eligibility_changes
```

---

## API Examples

### Manual Revalidation
```bash
POST /api/v1/jobs/42/revalidate-eligibility
Authorization: Bearer <recruiter_token>

Response:
{
  "job_id": 42,
  "job_title": "Software Engineer - Amazon",
  "revalidation_stats": {
    "total_applications": 120,
    "newly_eligible": 5,
    "newly_ineligible": 12,
    "still_eligible": 68,
    "still_ineligible": 35,
    "eligibility_changes": [
      {
        "application_id": 501,
        "student_id": 201,
        "change": "eligible_to_ineligible",
        "reasons": ["already_placed"]
      },
      {
        "application_id": 502,
        "student_id": 203,
        "change": "eligible_to_ineligible",
        "reasons": ["cgpa_below_threshold"]
      },
      {
        "application_id": 510,
        "student_id": 215,
        "change": "ineligible_to_eligible",
        "reasons": []
      }
    ]
  },
  "message": "Revalidated 120 applications. 12 became ineligible, 5 became eligible."
}
```

### Job Update Triggering Revalidation
```bash
PUT /api/v1/jobs/42
Authorization: Bearer <recruiter_token>

{
  "min_cgpa": 8.5,  # Raised from 7.5
  "exclude_placed_students": true  # Changed from false
}

# Server logs:
# [Jobs] Eligibility rules updated for job 42, triggering revalidation...
# [Eligibility] Application 501 became INELIGIBLE: already_placed
# [Eligibility] Application 502 became INELIGIBLE: cgpa_below_threshold
# [Jobs] Revalidation complete: 12 became ineligible, 0 became eligible
```

### Student Placement Update Triggering Revalidation
```bash
PUT /api/v1/students/me
Authorization: Bearer <student_token>

{
  "is_placed": true
}

# Server logs:
# [Students] Student 201 placement status changing: False -> True
# [Students] Revalidating eligibility for 8 applications...
# [Eligibility] Application 501 became INELIGIBLE: already_placed
# [Eligibility] Application 503 became INELIGIBLE: already_placed
# [Students] Revalidated 8 applications for student 201
```

### Ranking with Defensive Revalidation
```bash
POST /api/v1/jobs/42/rank
Authorization: Bearer <recruiter_token>

Response:
{
  "job_id": 42,
  "applications_ranked": 68,
  "applications_skipped_during_revalidation": 3,  # NEW
  "total_ranked_applications": 68,
  "eligible_count": 70,
  "ineligible_count": 50,
  "rejection_reasons": {
    "cgpa_below_threshold": 18,
    "already_placed": 15,
    "branch_not_allowed": 12,
    "exceeds_backlog_limit": 5
  },
  "message": "Ranking completed successfully with defensive revalidation"
}

# Server logs:
# [Orchestrator] Filtering eligible applications...
# [Orchestrator] Found 71 eligible applications
# [Orchestrator] Revalidating eligibility for application 501...
# [Orchestrator] Application 501 became ineligible: already_placed
# [Orchestrator] Revalidating eligibility for application 502...
# [Orchestrator] Application 502 became ineligible: cgpa_below_threshold
# [Orchestrator] Revalidating eligibility for application 503...
# [Orchestrator] Application 503 became ineligible: already_placed
# [Orchestrator] Scored 68 eligible applications, skipped 3 that became ineligible
```

---

## Testing Scenarios

### Test 1: Stale Eligibility - Student Gets Placed
```python
# 1. Student applies to job (exclude_placed_students=True)
POST /api/v1/applications
{
  "job_id": 42,
  "student_id": 201
}
# Result: is_eligible=True (student not placed yet)

# 2. Student gets placed
PUT /api/v1/students/me
{
  "is_placed": true
}
# Expected: Application 501 revalidated, becomes ineligible

# 3. Verify eligibility updated
GET /api/v1/applications/501
# Expected:
# {
#   "is_eligible": false,
#   "status": "ELIGIBILITY_FAILED",
#   "eligibility_reasons": ["already_placed"]
# }

# 4. Trigger ranking
POST /api/v1/jobs/42/rank
# Expected: Application 501 NOT included in ranking
```

### Test 2: Stale Eligibility - CGPA Requirement Raised
```python
# 1. Job has min_cgpa=7.5, student has 7.8
# Student applies, marked eligible

# 2. Recruiter raises bar
PUT /api/v1/jobs/42
{
  "min_cgpa": 8.0
}
# Expected: Automatic revalidation, student's application becomes ineligible

# 3. Verify revalidation
GET /api/v1/applications?job_id=42&is_eligible=false
# Expected: Student's application in ineligible list

# 4. Recruiter lowers bar again
PUT /api/v1/jobs/42
{
  "min_cgpa": 7.5
}
# Expected: Application becomes eligible again
```

### Test 3: Defensive Revalidation During Ranking
```python
# 1. 100 applications submitted, all marked eligible
# 2. Before ranking runs, 5 students get placed
# 3. Ranking triggered

# Expected flow:
# - Initial filter finds 100 eligible applications
# - During scoring loop:
#   - Revalidate application 1: still eligible, score it
#   - Revalidate application 10: NOW INELIGIBLE (placed), skip
#   - Revalidate application 15: NOW INELIGIBLE (placed), skip
#   - ...
# - Final result:
#   - applications_ranked: 95
#   - applications_skipped_during_revalidation: 5
```

### Test 4: Manual Revalidation
```python
# 1. Submit 50 applications
# 2. 10 students get placed externally (no API call)
# 3. Placement officer manually triggers revalidation

POST /api/v1/jobs/42/revalidate-eligibility
# Expected response:
# {
#   "total_applications": 50,
#   "newly_ineligible": 10,
#   "newly_eligible": 0,
#   "eligibility_changes": [
#     {"application_id": 501, "change": "eligible_to_ineligible", "reasons": ["already_placed"]},
#     ...
#   ]
# }
```

---

## Performance Impact

### Without Revalidation (OLD)
```
100 applications → All marked eligible at submission
    ↓
5 students get placed (eligibility becomes stale)
    ↓
AI ranking processes all 100 applications
    ↓
Waste: 5 embeddings + 5 AI scores for ineligible students
```

### With Defensive Revalidation (NEW)
```
100 applications → All marked eligible at submission
    ↓
5 students get placed
    ↓
Option 1: Student update triggers immediate revalidation
    ↓ 5 applications marked ineligible immediately
    
Option 2: Ranking revalidates before scoring
    ↓ Detectsapplications marked ineligible
    ↓ Skips 5 applications during scoring
    ↓
AI ranking processes only 95 applications
    ↓
Savings: 5 embeddings + 5 AI scores
```

### Revalidation Cost
- **Per application**: ~10ms (rule evaluation, no AI)
- **100 applications**: ~1 second total
- **AI scoring**: ~500ms per application
- **Savings**: Skip 5 ineligible = save ~2.5 seconds of AI time

**Trade-off**: Spend 1 second on revalidation, save 2.5+ seconds on AI

---

## Conclusion

All revalidation mechanisms implemented:

✅ **Defensive revalidation** in ranking orchestrator (before each AI scoring)
✅ **Automatic revalidation** when job eligibility rules updated
✅ **Automatic revalidation** when student placement status changes
✅ **Manual revalidation endpoint** for on-demand rechecking
✅ **Comprehensive revalidation service** tracking bidirectional eligibility changes
✅ **Detailed statistics** showing stale eligibility detection

**Guarantees**:
- AI ranking never processes applications with stale eligibility
- Eligibility changes detected and logged
- Fair rankings computed only among currently eligible candidates
- Performance optimized (skip scoring for ineligible applications)
