"""
Ranking Orchestrator Module

Orchestrates the end-to-end candidate ranking process:
1. Fetch job and applications
2. FILTER by eligibility rules (NEW - multi-tenant upgrade)
3. Extract job features (compute job embedding ONCE)
4. Extract candidate features for all eligible applicants
5. Score all eligible candidates using the scoring engine
6. Persist scores and assign ranks among eligible pool
7. Generate AI summaries

Key optimizations:
- Job embedding computed only once per ranking execution
- Eligibility filtering BEFORE AI (saves AI resources on ineligible candidates)
- Multi-tenant isolation enforced

Multi-tenant security:
- Only students from job's college can apply
- Eligibility checked at college level
- AI ranking only processes eligible candidates
"""

import json
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.job import Job
from app.models.student import Student
from app.models.resume import Resume
from app.models.application import Application, ApplicationStatus
from app.matching.feature_extractor import FeatureExtractor
from app.matching.scoring_engine import ScoringEngine, ScoreBreakdown
from app.eligibility import EligibilityService  # NEW

# Gemini AI — optional, graceful fallback if not available
try:
    import google.generativeai as genai
    from app.core.config import get_settings
    _settings = get_settings()
    if _settings.GEMINI_API_KEY:
        genai.configure(api_key=_settings.GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel(_settings.GEMINI_MODEL_NAME)
        GEMINI_AVAILABLE = True
        print("[AI] Google Gemini AI initialized successfully ✅")
    else:
        GEMINI_AVAILABLE = False
        print("[AI] Gemini API key not set — using rule-based summaries")
except Exception as e:
    GEMINI_AVAILABLE = False
    print(f"[AI] Gemini not available, using rule-based summaries: {e}")


class RankingOrchestrator:
    """
    Orchestrates the entire candidate ranking workflow.
    
    Ensures:
    - Job embedding computed exactly once
    - Eligibility filtering BEFORE AI ranking (NEW)
    - Multi-tenant data isolation (NEW)
    - Efficient batch processing
    - Database transactions handled properly
    """
    
    def __init__(self):
        """Initialize orchestrator with feature extractor, scoring engine, and eligibility service."""
        self.feature_extractor = FeatureExtractor()
        self.scoring_engine = ScoringEngine()
        self.eligibility_service = EligibilityService()  # NEW
    
    def _generate_ai_summary(
        self,
        job_title: str,
        candidate_name: str,
        candidate_cgpa: float,
        candidate_university: str,
        score_breakdown: ScoreBreakdown
    ) -> Dict[str, Any]:
        """
        Generate AI summary of candidate fit using Google Gemini.
        Falls back to rule-based summary if Gemini is unavailable.
        """
        # Try Gemini first
        if GEMINI_AVAILABLE:
            try:
                prompt = f"""You are a campus placement expert. Analyze this candidate's fit for a job.

Job Title: {job_title}
Candidate: {candidate_name}
University: {candidate_university or 'Not specified'}
CGPA: {candidate_cgpa or 'Not specified'}
Match Scores:
- Overall Match: {score_breakdown.overall_score:.1f}/100
- Skills Match: {score_breakdown.skills_score:.1f}/100
- Experience Match: {score_breakdown.experience_score:.1f}/100
- Semantic Fit: {score_breakdown.semantic_score:.1f}/100

Respond ONLY in this exact JSON format (no extra text):
{{
  "summary": "One sentence summary of the candidate's fit",
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1"]
}}"""
                response = _gemini_model.generate_content(prompt)
                text = response.text.strip()
                # Clean up markdown code blocks if present
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                result = json.loads(text.strip())
                return result
            except Exception as e:
                print(f"[AI] Gemini summary failed, using rule-based: {e}")

        # Rule-based fallback
        strengths = []
        weaknesses = []

        if score_breakdown.skills_score >= 70:
            strengths.append("Strong alignment with required technical skills")
        elif score_breakdown.skills_score < 40:
            weaknesses.append("Limited match with required technical skills")

        if score_breakdown.experience_score >= 80:
            strengths.append("Meets or exceeds experience requirements")
        elif score_breakdown.experience_score < 50:
            weaknesses.append("May lack required experience level")

        if candidate_cgpa and candidate_cgpa >= 8.0:
            strengths.append(f"Excellent academic performance (CGPA: {candidate_cgpa:.2f})")

        if candidate_university:
            strengths.append(f"Educational background from {candidate_university}")

        if score_breakdown.semantic_score >= 75:
            strengths.append("Strong semantic alignment with job requirements")

        if score_breakdown.overall_score >= 80:
            summary = f"Excellent candidate for {job_title}. Strong overall fit with high compatibility across multiple dimensions."
        elif score_breakdown.overall_score >= 60:
            summary = f"Good candidate for {job_title}. Demonstrates solid alignment with job requirements."
        elif score_breakdown.overall_score >= 40:
            summary = f"Moderate fit for {job_title}. Shows potential but may need development in some areas."
        else:
            summary = f"Limited fit for {job_title}. Significant gaps in required qualifications."

        return {
            "summary": summary,
            "strengths": strengths,
            "weaknesses": weaknesses
        }
    
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
        
        Args:
            db: Database session
            job_id: Job ID to rank applications for
            rerank: Whether to recalculate scores for already-scored applications
            
        Returns:
            Dictionary with ranking statistics
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
        
        # Step 3: FILTER ELIGIBLE APPLICATIONS (NEW - Multi-tenant upgrade)
        print(f"[Orchestrator] Filtering eligible applications...")
        eligible_applications = await self.eligibility_service.filter_eligible_applications(
            db=db,
            job_id=job_id,
            check_all=rerank  # Force recheck if reranking
        )
        
        print(f"[Orchestrator] Found {len(eligible_applications)} eligible applications")
        
        if not eligible_applications:
            # Get stats on why applications failed
            stats = await self.eligibility_service.get_eligibility_stats(db, job_id)
            return {
                "job_id": job_id,
                "applications_ranked": 0,
                "eligible_count": 0,
                "ineligible_count": stats.get("ineligible_count", 0),
                "rejection_reasons": stats.get("rejection_reasons", {}),
                "message": "No eligible applications to rank"
            }
        
        # Step 4: Process ONLY ELIGIBLE applications with DEFENSIVE REVALIDATION
        applications = eligible_applications
        scored_count = 0
        skipped_count = 0
        
        for application in applications:
            try:
                # Fetch student
                student_result = await db.execute(
                    select(Student).filter(Student.id == application.student_id)
                )
                student = student_result.scalar_one()
                
                # ===== DEFENSIVE REVALIDATION: Check eligibility before scoring =====
                # This catches stale eligibility due to:
                # - Job eligibility rules updated after initial check
                # - Student placement status changed
                # - Student data updated (CGPA, backlogs, etc.)
                print(f"[Orchestrator] Revalidating eligibility for application {application.id}...")
                is_still_eligible, failure_reasons = await self.eligibility_service.check_application_eligibility(
                    db=db,
                    application=application,
                    update_db=True  # Update DB if eligibility changed
                )
                
                if not is_still_eligible:
                    print(f"[Orchestrator] Application {application.id} became ineligible: {', '.join(failure_reasons)}")
                    skipped_count += 1
                    continue  # Skip scoring for now-ineligible applications
                
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
                # Continue processing other applications
                continue
        
        # Commit all scores
        await db.commit()
        print(f"[Orchestrator] Scored {scored_count} eligible applications")
        
        # Step 5: Assign ranks based on match scores (ONLY among eligible pool)
        ranked_result = await db.execute(
            select(Application)
            .filter(Application.job_id == job_id)
            .filter(Application.is_eligible == True)  # CRITICAL: Only rank eligible
            .filter(Application.match_score.isnot(None))
            .order_by(Application.match_score.desc())
        )
        ranked_applications = ranked_result.scalars().all()
        
        for rank, app in enumerate(ranked_applications, start=1):
            app.rank = rank
            app.rank_among_eligible = rank  # Explicit: rank among eligible only
        
        await db.commit()
        print(f"[Orchestrator] Assigned ranks to {len(ranked_applications)} eligible applications")
        
        # Step 6: Get eligibility stats for reporting
        eligibility_stats = await self.eligibility_service.get_eligibility_stats(db, job_id)
        
        return {
            "job_id": job_id,
            "applications_ranked": scored_count,
            "applications_skipped_during_revalidation": skipped_count,  # NEW: Track stale eligibility
            "total_ranked_applications": len(ranked_applications),
            "eligible_count": eligibility_stats.get("eligible_count", 0),
            "ineligible_count": eligibility_stats.get("ineligible_count", 0),
            "not_checked_count": eligibility_stats.get("not_checked_count", 0),
            "rejection_reasons": eligibility_stats.get("rejection_reasons", {}),
            "message": "Ranking completed successfully with defensive revalidation"
        }
    
    async def score_single_application(
        self,
        db: AsyncSession,
        application_id: int
    ) -> Dict[str, Any]:
        """
        Score a single application (used for real-time scoring on submission).
        
        Now includes eligibility checking (NEW - multi-tenant upgrade).
        If application is ineligible, returns eligibility failure instead of scoring.
        
        Args:
            db: Database session
            application_id: Application ID to score
            
        Returns:
            Dictionary with scoring results or eligibility failure
        """
        # Fetch application
        app_result = await db.execute(
            select(Application).filter(Application.id == application_id)
        )
        application = app_result.scalar_one_or_none()
        
        if not application:
            raise ValueError(f"Application {application_id} not found")
        
        # Step 1: Check eligibility FIRST (NEW)
        is_eligible, failure_reasons = await self.eligibility_service.check_application_eligibility(
            db=db,
            application=application,
            update_db=True  # Mark in database
        )
        
        if not is_eligible:
            return {
                "application_id": application_id,
                "is_eligible": False,
                "failure_reasons": failure_reasons,
                "message": "Application failed eligibility check - NOT scored",
                "status": "eligibility_failed"
            }
        
        # Step 2: If eligible, proceed with AI scoring
        # Fetch job
        job_result = await db.execute(select(Job).filter(Job.id == application.job_id))
        job = job_result.scalar_one()
        
        # Fetch student
        student_result = await db.execute(
            select(Student).filter(Student.id == application.student_id)
        )
        student = student_result.scalar_one()
        
        # Fetch resume (optional)
        resume = None
        if application.resume_id:
            resume_result = await db.execute(
                select(Resume).filter(Resume.id == application.resume_id)
            )
            resume = resume_result.scalar_one_or_none()
        
        # Extract features
        job_features = self.feature_extractor.extract_job_features(job)
        candidate_features = self.feature_extractor.extract_candidate_features(
            application_id=application.id,
            student=student,
            resume=resume,
            compute_embedding=True
        )
        
        # Score candidate
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
        
        # Update application
        application.match_score = score_breakdown.overall_score
        application.skills_match_score = score_breakdown.skills_score
        application.experience_match_score = score_breakdown.experience_score
        application.ai_summary = ai_summary["summary"]
        application.strengths = json.dumps(ai_summary["strengths"])
        application.weaknesses = json.dumps(ai_summary["weaknesses"])
        
        await db.commit()
        
        return {
            "application_id": application_id,
            "is_eligible": True,  # NEW: Explicit eligibility status
            "scores": score_breakdown.to_dict(),
            "summary": ai_summary,
            "message": "Application scored successfully",
            "status": "scored"
        }
