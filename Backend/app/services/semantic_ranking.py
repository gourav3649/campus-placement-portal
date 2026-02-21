import json
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.application import Application
from app.models.job import Job
from app.models.student import Student
from app.models.resume import Resume


class SemanticRankingService:
    """
    AI-powered semantic ranking service for matching candidates to jobs.
    
    Uses sentence transformers for embedding generation and cosine similarity
    for semantic matching.
    """
    
    def __init__(self):
        """Initialize the semantic ranking service."""
        # Load sentence transformer model for embeddings
        self.model = None  # Lazy load
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
    
    def _get_model(self):
        """Lazy load the embedding model."""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
        return self.model
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as list of floats
        """
        model = self._get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1)
        """
        # Convert to numpy arrays
        vec1 = np.array(embedding1).reshape(1, -1)
        vec2 = np.array(embedding2).reshape(1, -1)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(vec1, vec2)[0][0]
        
        return float(similarity)
    
    def extract_job_requirements(self, job: Job) -> str:
        """
        Extract and format job requirements into a searchable text.
        
        Args:
            job: Job object
            
        Returns:
            Formatted job requirements text
        """
        requirements_text = f"""
        Job Title: {job.title}
        Description: {job.description}
        Requirements: {job.requirements or ''}
        Responsibilities: {job.responsibilities or ''}
        Required Skills: {job.required_skills or ''}
        Experience Required: {job.experience_years or 0} years
        Education Level: {job.education_level or 'Not specified'}
        """
        return requirements_text.strip()
    
    def extract_candidate_profile(self, student: Student, resume: Optional[Resume]) -> str:
        """
        Extract and format candidate profile into searchable text.
        
        Args:
            student: Student object
            resume: Resume object (optional)
            
        Returns:
            Formatted candidate profile text
        """
        profile_text = f"""
        Name: {student.first_name} {student.last_name}
        Education: {student.degree or ''} in {student.major or ''}
        University: {student.university or ''}
        CGPA: {student.cgpa or 'N/A'}
        Skills: {student.skills or ''}
        Bio: {student.bio or ''}
        """
        
        if resume and resume.raw_text:
            profile_text += f"\nResume Content: {resume.raw_text[:2000]}"  # Limit resume text
        
        return profile_text.strip()
    
    def calculate_skills_match(self, job_skills: str, candidate_skills: str) -> float:
        """
        Calculate skills match score.
        
        Args:
            job_skills: Required skills from job
            candidate_skills: Candidate's skills
            
        Returns:
            Skills match score (0-100)
        """
        if not job_skills or not candidate_skills:
            return 0.0
        
        # Parse skills (assume comma-separated)
        job_skill_set = set([s.strip().lower() for s in job_skills.split(',') if s.strip()])
        candidate_skill_set = set([s.strip().lower() for s in candidate_skills.split(',') if s.strip()])
        
        if not job_skill_set:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = job_skill_set.intersection(candidate_skill_set)
        union = job_skill_set.union(candidate_skill_set)
        
        jaccard_score = len(intersection) / len(union) if union else 0
        
        # Also use semantic similarity
        job_skills_text = ' '.join(job_skill_set)
        candidate_skills_text = ' '.join(candidate_skill_set)
        
        job_embedding = self.generate_embedding(job_skills_text)
        candidate_embedding = self.generate_embedding(candidate_skills_text)
        
        semantic_score = self.calculate_similarity(job_embedding, candidate_embedding)
        
        # Combined score (weighted average)
        combined_score = (jaccard_score * 0.4 + semantic_score * 0.6) * 100
        
        return min(100.0, combined_score)
    
    def calculate_experience_match(self, required_years: Optional[int], student: Student) -> float:
        """
        Calculate experience match score.
        
        This is a simplified version. In production, parse actual experience from resume.
        
        Args:
            required_years: Required years of experience
            student: Student object
            
        Returns:
            Experience match score (0-100)
        """
        if not required_years or required_years == 0:
            return 100.0  # No experience required
        
        # For students, we typically assume limited experience
        # This would be better calculated from parsed resume data
        # For now, give partial credit based on academic year
        
        if student.graduation_year:
            from datetime import datetime
            current_year = datetime.now().year
            years_in_school = max(0, current_year - (student.graduation_year - 4))
            
            if years_in_school >= required_years:
                return 100.0
            else:
                return (years_in_school / required_years) * 100
        
        return 50.0  # Default moderate score
    
    async def calculate_match_score(
        self,
        job: Job,
        student: Student,
        resume: Optional[Resume]
    ) -> Dict[str, float]:
        """
        Calculate comprehensive match score for a candidate and job.
        
        Args:
            job: Job object
            student: Student object
            resume: Resume object
            
        Returns:
            Dictionary with match scores
        """
        # Extract profiles
        job_text = self.extract_job_requirements(job)
        candidate_text = self.extract_candidate_profile(student, resume)
        
        # Generate embeddings
        job_embedding = self.generate_embedding(job_text)
        candidate_embedding = self.generate_embedding(candidate_text)
        
        # Calculate overall semantic similarity
        overall_similarity = self.calculate_similarity(job_embedding, candidate_embedding)
        
        # Calculate specific match scores
        skills_match = self.calculate_skills_match(
            job.required_skills or "",
            student.skills or ""
        )
        
        experience_match = self.calculate_experience_match(
            job.experience_years,
            student
        )
        
        # Calculate weighted overall score
        overall_score = (
            overall_similarity * 0.4 +  # 40% overall semantic match
            (skills_match / 100) * 0.4 +  # 40% skills match
            (experience_match / 100) * 0.2  # 20% experience match
        ) * 100
        
        return {
            "match_score": round(overall_score, 2),
            "skills_match_score": round(skills_match, 2),
            "experience_match_score": round(experience_match, 2)
        }
    
    async def generate_ai_summary(
        self,
        job: Job,
        student: Student,
        match_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Generate AI summary of candidate fit.
        
        This is a rule-based summary. In production, use GPT for better summaries.
        
        Args:
            job: Job object
            student: Student object
            match_scores: Calculated match scores
            
        Returns:
            Dictionary with summary, strengths, and weaknesses
        """
        strengths = []
        weaknesses = []
        
        # Analyze skills match
        if match_scores["skills_match_score"] >= 70:
            strengths.append("Strong alignment with required technical skills")
        elif match_scores["skills_match_score"] < 40:
            weaknesses.append("Limited match with required technical skills")
        
        # Analyze experience
        if match_scores["experience_match_score"] >= 80:
            strengths.append("Meets or exceeds experience requirements")
        elif match_scores["experience_match_score"] < 50:
            weaknesses.append("May lack required experience level")
        
        # Analyze education
        if student.cgpa and student.cgpa >= 8.0:
            strengths.append("Excellent academic performance (CGPA: {:.2f})".format(student.cgpa))
        
        if student.university:
            strengths.append(f"Educational background from {student.university}")
        
        # Generate summary
        if match_scores["match_score"] >= 80:
            summary = f"Excellent candidate for {job.title}. Strong overall fit with high compatibility across multiple dimensions."
        elif match_scores["match_score"] >= 60:
            summary = f"Good candidate for {job.title}. Demonstrates solid alignment with job requirements."
        elif match_scores["match_score"] >= 40:
            summary = f"Moderate fit for {job.title}. Shows potential but may need development in some areas."
        else:
            summary = f"Limited fit for {job.title}. Significant gaps in required qualifications."
        
        return {
            "summary": summary,
            "strengths": strengths,
            "weaknesses": weaknesses
        }


# Global service instance
_ranking_service = SemanticRankingService()


async def process_application_matching(application_id: int):
    """
    Background task to process AI matching for a single application.
    
    REFACTORED: Now uses RankingOrchestrator for clean separation of concerns.
    
    Args:
        application_id: ID of the application to process
    """
    from app.matching.ranking_orchestrator import RankingOrchestrator
    
    async with AsyncSessionLocal() as db:
        try:
            orchestrator = RankingOrchestrator()
            result = await orchestrator.score_single_application(db, application_id)
            print(f"[Background Task] Application {application_id} scored: {result['scores']['match_score']}")
            
        except Exception as e:
            print(f"Error processing application matching: {str(e)}")
            await db.rollback()


async def rank_job_applications(job_id: int, rerank: bool = False):
    """
    Background task to rank all applications for a job.
    
    REFACTORED: Now uses RankingOrchestrator for optimized ranking.
    
    Key improvements:
    - Job embedding computed ONCE (not per candidate)
    - Clean separation of concerns (feature extraction, scoring, orchestration)
    - Batch processing with proper error handling
    
    Args:
        job_id: ID of the job
        rerank: Whether to recalculate scores for already-processed applications
    """
    from app.matching.ranking_orchestrator import RankingOrchestrator
    
    async with AsyncSessionLocal() as db:
        try:
            orchestrator = RankingOrchestrator()
            result = await orchestrator.rank_applications(db, job_id, rerank)
            
            print(f"[Background Task] Ranking completed for job {job_id}")
            print(f"[Background Task] Applications ranked: {result['applications_ranked']}")
            print(f"[Background Task] Total ranked applications: {result['total_ranked_applications']}")
            
        except Exception as e:
            print(f"Error ranking job applications: {str(e)}")
            await db.rollback()
