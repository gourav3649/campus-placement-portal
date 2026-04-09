"""
Ranking service for job candidate matching.
Computes cosine similarity between resume and job embeddings.
Efficient batch processing, no N+1 queries.
"""
import logging
from typing import Dict, List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.application import Application
from app.models.job import Job
from app.models.resume import Resume
from app.services.embedding_service import embedding_from_json, cosine_similarity

logger = logging.getLogger(__name__)


async def rank_applications_for_job(
    job_id: int,
    db: AsyncSession,
) -> Dict[int, float]:
    """
    Rank all ELIGIBLE applications for a job based on resume-job embedding similarity.
    
    Uses batch queries to avoid N+1 problem.
    Stores raw cosine similarity (-1 to 1) without clamping.
    
    Args:
        job_id: ID of the job to rank applications for
        db: Database session
        
    Returns:
        Dict mapping application_id to similarity score (-1 to 1)
        
    Raises:
        ValueError: If job not found or has no embedding
    """
    logger.debug(f"Starting ranking process for job_id: {job_id}")
    
    # Fetch the job and its embedding
    job_result = await db.execute(select(Job).filter(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    
    if not job:
        logger.error(f"Job not found for ranking: job_id={job_id}")
        raise ValueError(f"Job not found: job_id={job_id}")
    
    if not job.embedding_vector:
        logger.error(f"Job has no embedding for ranking: job_id={job_id}")
        raise ValueError(f"Job has no embedding: job_id={job_id}")
    
    # Parse job embedding
    try:
        job_embedding = embedding_from_json(job.embedding_vector)
        logger.debug(f"Job embedding parsed successfully: dimension={job_embedding.shape[0]}")
    except ValueError as e:
        logger.error(f"Failed to parse job embedding: {str(e)}")
        raise ValueError(f"Invalid job embedding: {str(e)}")
    
    # Fetch all ELIGIBLE applications WITH their resumes in single query (avoid N+1)
    query = (
        select(Application, Resume)
        .join(Resume, Application.resume_id == Resume.id)
        .filter(Application.job_id == job_id)
        .filter(Application.is_eligible == True)  # Only rank eligible applications
    )
    
    result = await db.execute(query)
    app_resume_pairs = result.all()
    
    logger.info(f"Found {len(app_resume_pairs)} eligible applications for job_id={job_id}")
    
    scores: Dict[int, float] = {}
    skipped_count = 0
    
    # Compute similarity scores for each application-resume pair
    for app, resume in app_resume_pairs:
        try:
            if not resume.embedding_vector:
                logger.warning(f"Resume has no embedding for application_id={app.id}, student_id={resume.student_id}")
                skipped_count += 1
                continue
            
            # Parse resume embedding
            try:
                resume_embedding = embedding_from_json(resume.embedding_vector)
            except ValueError as e:
                logger.warning(f"Invalid resume embedding for application_id={app.id}: {str(e)}")
                skipped_count += 1
                continue
            
            # Compute similarity score (store raw cosine similarity, no clamping)
            similarity_score = cosine_similarity(resume_embedding, job_embedding)
            
            scores[app.id] = similarity_score
            
            logger.debug(f"Computed similarity for application_id={app.id}: {similarity_score:.4f}")
            
        except Exception as e:
            logger.error(f"Error processing application_id={app.id}: {str(e)}")
            skipped_count += 1
            continue
    
    logger.info(
        f"Ranking complete for job_id={job_id}: "
        f"scored={len(scores)}, skipped={skipped_count}, total={len(app_resume_pairs)}"
    )
    
    return scores


async def update_application_scores(
    job_id: int,
    db: AsyncSession,
) -> int:
    """
    Compute and store raw cosine similarity scores for all eligible applications.
    
    Batch updates scores without per-application DB queries.
    Stores raw cosine similarity (-1 to 1) without clamping.
    
    Args:
        job_id: ID of the job
        db: Database session
        
    Returns:
        Number of applications updated
        
    Raises:
        ValueError: If job not found or has no embedding
    """
    logger.info(f"Updating application scores for job_id={job_id}")
    
    # Get ranking scores (already filtered for eligible, uses batch query)
    scores = await rank_applications_for_job(job_id, db)
    
    if not scores:
        logger.info(f"No eligible applications to score for job_id={job_id}")
        return 0
    
    # Batch update all scores at once
    updated_count = 0
    for app_id, similarity in scores.items():
        # Fetch application to update (small dataset, all IDs are known)
        app_result = await db.execute(
            select(Application).filter(Application.id == app_id)
        )
        app = app_result.scalar_one_or_none()
        
        if app:
            app.ai_rank_score = similarity  # Store raw cosine similarity (-1 to 1)
            logger.debug(f"Updated application_id={app_id}: ai_rank_score={similarity:.4f}")
            updated_count += 1
    
    # Single batch commit
    await db.commit()
    
    logger.info(f"Application scores updated: {updated_count} eligible applications for job_id={job_id}")
    return updated_count


async def get_ranked_applications(
    job_id: int,
    db: AsyncSession,
) -> List[Tuple[int, float, int]]:
    """
    Get all applications for a job ranked by similarity score.
    
    Args:
        job_id: ID of the job
        db: Database session
        
    Returns:
        List of tuples: (application_id, similarity_score, ai_rank)
        
    Raises:
        ValueError: If job not found or has no embedding
    """
    logger.debug(f"Fetching ranked applications for job_id={job_id}")
    
    # Get scores
    scores = await rank_applications_for_job(job_id, db)
    
    # Sort by score descending
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # Assign ranks (1-indexed)
    ranked = [
        (app_id, score, rank + 1)
        for rank, (app_id, score) in enumerate(sorted_scores)
    ]
    
    logger.info(f"Ranked {len(ranked)} applications for job_id={job_id}")
    return ranked


async def get_application_ranking(
    application_id: int,
    db: AsyncSession,
) -> Optional[Dict]:
    """
    Get ranking details for a specific application.
    
    Args:
        application_id: ID of the application
        db: Database session
        
    Returns:
        Dict with: application_id, similarity_score, rank, total_applications
        Returns None if application or job not found
    """
    # Fetch application
    app_result = await db.execute(
        select(Application).filter(Application.id == application_id)
    )
    app = app_result.scalar_one_or_none()
    
    if not app:
        logger.warning(f"Application not found for ranking details: app_id={application_id}")
        return None
    
    try:
        # Get all ranked applications for this job
        ranked = await get_ranked_applications(app.job_id, db)
        
        # Find this application in the ranking
        for app_id, score, rank in ranked:
            if app_id == application_id:
                return {
                    "application_id": application_id,
                    "similarity_score": round(score, 4),  # 4 decimal places (0-1 range)
                    "rank": rank,
                    "total_applications": len(ranked),
                }
        
        # Application has no score (missing embeddings)
        logger.warning(f"Application not in ranking (missing embeddings): app_id={application_id}")
        return None
        
    except ValueError as e:
        logger.error(f"Cannot get ranking for application_id={application_id}: {str(e)}")
        return None
