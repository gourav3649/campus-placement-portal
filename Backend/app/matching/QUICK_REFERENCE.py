"""
Matching Engine - Quick Reference Guide

This file shows all necessary imports and usage patterns
for the refactored matching engine architecture.
"""

# =============================================================================
# IMPORTS - Use these in your code
# =============================================================================

# From the matching module (new architecture)
from app.matching import (
    RankingOrchestrator,        # Main orchestrator
    FeatureExtractor,            # Feature extraction
    ScoringEngine,               # Scoring logic
    CandidateFeatures,           # Data class
    JobFeatures,                 # Data class
    ScoreBreakdown,              # Data class
)

# From services (backward compatibility)
from app.services.semantic_ranking import (
    process_application_matching,   # Background task for single app
    rank_job_applications,          # Background task for batch ranking
)

# Database
from app.database import get_db, AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession

# Models
from app.models.job import Job
from app.models.student import Student
from app.models.resume import Resume
from app.models.application import Application


# =============================================================================
# USAGE PATTERN 1: Use RankingOrchestrator Directly (Recommended)
# =============================================================================

async def example_rank_job_applications(job_id: int):
    """Rank all applications for a job using the new architecture."""
    
    async with AsyncSessionLocal() as db:
        # Create orchestrator
        orchestrator = RankingOrchestrator()
        
        # Rank all applications
        result = await orchestrator.rank_applications(
            db=db,
            job_id=job_id,
            rerank=False  # Set True to recalculate existing scores
        )
        
        print(f"Applications ranked: {result['applications_ranked']}")
        print(f"Total ranked: {result['total_ranked_applications']}")
        
        return result


async def example_score_single_application(application_id: int):
    """Score a single application (real-time on submission)."""
    
    async with AsyncSessionLocal() as db:
        orchestrator = RankingOrchestrator()
        
        result = await orchestrator.score_single_application(
            db=db,
            application_id=application_id
        )
        
        print(f"Match Score: {result['scores']['match_score']}")
        print(f"Skills Score: {result['scores']['skills_match_score']}")
        print(f"Semantic Score: {result['scores']['semantic_similarity']}")
        
        return result


# =============================================================================
# USAGE PATTERN 2: Use Background Tasks (Backward Compatible)
# =============================================================================

async def example_background_ranking(job_id: int):
    """Use existing background task functions (backward compatible)."""
    
    # These functions internally use RankingOrchestrator
    await rank_job_applications(job_id=job_id, rerank=False)
    

async def example_background_single_app(application_id: int):
    """Score single application via background task."""
    
    await process_application_matching(application_id=application_id)


# =============================================================================
# USAGE PATTERN 3: Use Individual Components (Advanced)
# =============================================================================

async def example_custom_scoring_pipeline(job_id: int):
    """Build custom scoring pipeline using individual components."""
    
    async with AsyncSessionLocal() as db:
        # Initialize components
        extractor = FeatureExtractor()
        engine = ScoringEngine()
        
        # Fetch job
        from sqlalchemy import select
        result = await db.execute(select(Job).filter(Job.id == job_id))
        job = result.scalar_one()
        
        # Extract job features (ONCE)
        job_features = extractor.extract_job_features(job)
        print(f"Job embedding computed: {len(job_features.job_embedding)} dimensions")
        
        # Fetch applications
        result = await db.execute(
            select(Application).filter(Application.job_id == job_id)
        )
        applications = result.scalars().all()
        
        # Score each candidate
        for app in applications:
            # Fetch student
            student_result = await db.execute(
                select(Student).filter(Student.id == app.student_id)
            )
            student = student_result.scalar_one()
            
            # Fetch resume (optional)
            resume = None
            if app.resume_id:
                resume_result = await db.execute(
                    select(Resume).filter(Resume.id == app.resume_id)
                )
                resume = resume_result.scalar_one_or_none()
            
            # Extract candidate features
            candidate_features = extractor.extract_candidate_features(
                application_id=app.id,
                student=student,
                resume=resume
            )
            
            # Score using PRECOMPUTED job features
            scores = engine.score_candidate(
                job_features=job_features,  # Reused for all candidates
                candidate_features=candidate_features
            )
            
            # Update application
            app.match_score = scores.overall_score
            app.skills_match_score = scores.skills_score
            app.experience_match_score = scores.experience_score
            
            print(f"Scored application {app.id}: {scores.overall_score:.2f}")
        
        await db.commit()


# =============================================================================
# USAGE PATTERN 4: API Endpoint Integration
# =============================================================================

from fastapi import APIRouter, Depends, BackgroundTasks
from app.api.deps import get_current_recruiter

router = APIRouter()

@router.post("/jobs/{job_id}/rank")
async def api_rank_job_applications(
    job_id: int,
    background_tasks: BackgroundTasks,
    current_recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """
    API endpoint to trigger ranking for a job.
    
    Uses background task for async processing.
    """
    # Verify recruiter owns the job
    from sqlalchemy import select
    result = await db.execute(select(Job).filter(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job or job.recruiter_id != current_recruiter.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Trigger ranking in background
    background_tasks.add_task(rank_job_applications, job_id, False)
    
    return {
        "message": "Ranking triggered successfully",
        "job_id": job_id,
        "status": "processing"
    }


@router.post("/applications")
async def api_submit_application(
    job_id: int,
    resume_id: int,
    background_tasks: BackgroundTasks,
    current_student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit application and score in background.
    """
    # Create application
    application = Application(
        student_id=current_student.id,
        job_id=job_id,
        resume_id=resume_id,
        status="pending"
    )
    
    db.add(application)
    await db.commit()
    await db.refresh(application)
    
    # Score in background
    background_tasks.add_task(process_application_matching, application.id)
    
    return {
        "application_id": application.id,
        "message": "Application submitted. Scoring in progress."
    }


# =============================================================================
# DATA STRUCTURES - Reference
# =============================================================================

def example_data_structures():
    """Examples of data structures used in matching engine."""
    
    # CandidateFeatures
    candidate = CandidateFeatures(
        student_id=1,
        application_id=10,
        name="John Doe",
        skills=["Python", "React", "PostgreSQL"],
        experience_years=2.5,
        education="B.S. in Computer Science",
        cgpa=8.5,
        university="MIT",
        profile_embedding=[0.1, 0.2, ...],  # 384-dim vector
        raw_profile_text="Full profile text...",
        resume_text="Resume content..."
    )
    
    # JobFeatures
    job = JobFeatures(
        job_id=5,
        title="Backend Developer",
        required_skills=["Python", "FastAPI", "PostgreSQL"],
        required_experience_years=2,
        education_level="Bachelor's",
        job_embedding=[0.3, 0.4, ...],  # 384-dim vector (computed ONCE)
        raw_job_text="Full job description..."
    )
    
    # ScoreBreakdown
    scores = ScoreBreakdown(
        overall_score=78.5,      # 0-100 weighted score
        semantic_score=82.3,     # 0-100 semantic similarity
        skills_score=75.0,       # 0-100 skills match
        experience_score=80.0    # 0-100 experience match
    )
    
    # Convert to dict for API response
    scores_dict = scores.to_dict()
    # {
    #     "match_score": 78.5,
    #     "semantic_similarity": 82.3,
    #     "skills_match_score": 75.0,
    #     "experience_match_score": 80.0
    # }


# =============================================================================
# PERFORMANCE OPTIMIZATION EXAMPLES
# =============================================================================

async def example_optimized_batch_scoring(job_id: int):
    """
    Demonstrates the key optimization: compute job embedding ONCE.
    
    For 100 candidates:
    - OLD: 200 embeddings (100 job + 100 candidate)
    - NEW: 101 embeddings (1 job + 100 candidate)
    - SAVINGS: 49.5% reduction in embedding computation
    """
    
    async with AsyncSessionLocal() as db:
        extractor = FeatureExtractor()
        engine = ScoringEngine()
        
        # Fetch job
        from sqlalchemy import select
        result = await db.execute(select(Job).filter(Job.id == job_id))
        job = result.scalar_one()
        
        # CRITICAL: Extract job features ONCE
        print("[Optimization] Computing job embedding ONCE...")
        job_features = extractor.extract_job_features(job)
        print(f"[Optimization] Job embedding ready ({len(job_features.job_embedding)} dims)")
        
        # Fetch all applications
        result = await db.execute(
            select(Application).filter(Application.job_id == job_id)
        )
        applications = result.scalars().all()
        
        print(f"[Optimization] Processing {len(applications)} candidates...")
        print(f"[Optimization] Job embedding will be REUSED {len(applications)} times")
        
        # Score all candidates using the SAME job_features
        for i, app in enumerate(applications, 1):
            # ... fetch student and resume ...
            
            candidate_features = extractor.extract_candidate_features(...)
            
            # This uses the PRECOMPUTED job embedding (no recomputation)
            scores = engine.score_candidate(
                job_features=job_features,  # ← REUSED from line 234
                candidate_features=candidate_features
            )
            
            app.match_score = scores.overall_score
            
            if i % 10 == 0:
                print(f"[Optimization] Scored {i}/{len(applications)} candidates")
        
        await db.commit()
        
        print("[Optimization] Completed!")
        print(f"[Optimization] Embeddings computed: {1 + len(applications)}")
        print(f"[Optimization] OLD would have computed: {2 * len(applications)}")


# =============================================================================
# ERROR HANDLING EXAMPLES
# =============================================================================

async def example_error_handling(job_id: int):
    """Proper error handling with rollback."""
    
    async with AsyncSessionLocal() as db:
        try:
            orchestrator = RankingOrchestrator()
            
            result = await orchestrator.rank_applications(
                db=db,
                job_id=job_id,
                rerank=False
            )
            
            print(f"Success: {result['applications_ranked']} applications ranked")
            
        except ValueError as e:
            print(f"Validation error: {str(e)}")
            await db.rollback()
            
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            await db.rollback()
            raise


# =============================================================================
# TESTING EXAMPLES
# =============================================================================

async def test_scoring_engine():
    """Unit test for scoring engine."""
    from app.matching import ScoringEngine, CandidateFeatures, JobFeatures
    
    engine = ScoringEngine()
    
    # Mock job features
    job_features = JobFeatures(
        job_id=1,
        title="Backend Developer",
        required_skills=["Python", "FastAPI", "PostgreSQL"],
        required_experience_years=2,
        education_level="Bachelor's",
        job_embedding=[0.5] * 384,  # Mock embedding
        raw_job_text="..."
    )
    
    # Mock candidate features
    candidate_features = CandidateFeatures(
        student_id=1,
        application_id=1,
        name="John Doe",
        skills=["Python", "FastAPI", "Docker"],
        experience_years=3.0,
        education="B.S. Computer Science",
        cgpa=8.5,
        university="MIT",
        profile_embedding=[0.6] * 384,  # Mock embedding
        raw_profile_text="...",
        resume_text="..."
    )
    
    # Score
    scores = engine.score_candidate(job_features, candidate_features)
    
    # Assertions
    assert 0 <= scores.overall_score <= 100
    assert 0 <= scores.semantic_score <= 100
    assert 0 <= scores.skills_score <= 100
    assert 0 <= scores.experience_score <= 100
    
    print(f"Test passed! Overall score: {scores.overall_score:.2f}")


# =============================================================================
# MONITORING & LOGGING
# =============================================================================

import logging

logger = logging.getLogger(__name__)

async def example_with_logging(job_id: int):
    """Example with proper logging for production."""
    
    logger.info(f"Starting ranking for job {job_id}")
    
    async with AsyncSessionLocal() as db:
        try:
            orchestrator = RankingOrchestrator()
            
            logger.debug("Extracting job features...")
            result = await orchestrator.rank_applications(db, job_id, False)
            
            logger.info(
                f"Ranking completed for job {job_id}: "
                f"{result['applications_ranked']} applications scored"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error ranking job {job_id}: {str(e)}", exc_info=True)
            await db.rollback()
            raise


# =============================================================================
# SUMMARY
# =============================================================================

"""
Key Takeaways:

1. ALWAYS use RankingOrchestrator for ranking operations
2. Job embedding is computed ONCE per ranking execution
3. Use background tasks for async processing
4. Proper error handling with rollback
5. Structured data classes for type safety
6. 40/40/20 formula preserved exactly
7. Backward compatible with existing API

Performance:
- 49.5% reduction in embedding computations
- Cleaner code with separation of concerns
- Better testability and maintainability
"""
