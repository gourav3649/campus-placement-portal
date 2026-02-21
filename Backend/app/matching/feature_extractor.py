"""
Feature Extractor Module

Extracts structured features from candidates and jobs for AI matching.
Ensures embeddings are computed efficiently (job embedding computed once per ranking).
"""

import json
from dataclasses import dataclass
from typing import List, Optional
from sentence_transformers import SentenceTransformer

from app.models.job import Job
from app.models.student import Student
from app.models.resume import Resume


@dataclass
class CandidateFeatures:
    """Structured candidate features for matching."""
    student_id: int
    application_id: int
    
    # Profile data
    name: str
    skills: List[str]
    experience_years: float
    education: str
    cgpa: Optional[float]
    university: Optional[str]
    
    # Embeddings
    profile_embedding: Optional[List[float]]
    
    # Raw data for advanced scoring
    raw_profile_text: str
    resume_text: Optional[str]


@dataclass
class JobFeatures:
    """Structured job features for matching."""
    job_id: int
    
    # Job requirements
    title: str
    required_skills: List[str]
    required_experience_years: int
    education_level: Optional[str]
    
    # Embeddings (computed ONCE)
    job_embedding: List[float]
    
    # Raw data
    raw_job_text: str


class FeatureExtractor:
    """
    Extracts features from candidates and jobs.
    
    Handles:
    - Skill parsing (comma-separated strings to lists)
    - Experience estimation from graduation year
    - Embedding generation (lazy-loaded model)
    - Text extraction for semantic matching
    """
    
    def __init__(self):
        """Initialize feature extractor with lazy-loaded model."""
        self.model = None
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
    
    def _get_model(self) -> SentenceTransformer:
        """Lazy load the sentence transformer model."""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
        return self.model
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.
        
        Args:
            text: Input text to embed
            
        Returns:
            384-dimensional embedding vector
        """
        model = self._get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def _parse_skills(self, skills_text: Optional[str]) -> List[str]:
        """
        Parse skills from comma-separated string.
        
        Args:
            skills_text: Comma-separated skills string
            
        Returns:
            List of cleaned skill strings
        """
        if not skills_text:
            return []
        
        return [s.strip() for s in skills_text.split(',') if s.strip()]
    
    def _estimate_experience_years(self, student: Student) -> float:
        """
        Estimate experience years from student data.
        
        For students, estimate based on graduation year.
        In production, parse from resume experience section.
        
        Args:
            student: Student object
            
        Returns:
            Estimated years of experience
        """
        if not student.graduation_year:
            return 0.0
        
        from datetime import datetime
        current_year = datetime.now().year
        
        # Assume 4-year degree, calculate years since enrollment
        years_since_enrollment = max(0, current_year - (student.graduation_year - 4))
        
        # Cap at reasonable values for students
        return min(years_since_enrollment, 5.0)
    
    def _build_candidate_text(self, student: Student, resume: Optional[Resume]) -> str:
        """
        Build comprehensive text representation of candidate.
        
        Args:
            student: Student object
            resume: Resume object (optional)
            
        Returns:
            Formatted text for embedding
        """
        profile_parts = [
            f"Name: {student.first_name} {student.last_name}",
            f"Education: {student.degree or ''} in {student.major or ''}",
            f"University: {student.university or ''}",
            f"CGPA: {student.cgpa or 'N/A'}",
            f"Skills: {student.skills or ''}",
            f"Bio: {student.bio or ''}",
        ]
        
        profile_text = "\n".join(profile_parts)
        
        # Append resume text (limited to avoid token limits)
        if resume and resume.raw_text:
            profile_text += f"\n\nResume Content:\n{resume.raw_text[:2000]}"
        
        return profile_text.strip()
    
    def _build_job_text(self, job: Job) -> str:
        """
        Build comprehensive text representation of job.
        
        Args:
            job: Job object
            
        Returns:
            Formatted text for embedding
        """
        job_parts = [
            f"Job Title: {job.title}",
            f"Description: {job.description}",
            f"Requirements: {job.requirements or ''}",
            f"Responsibilities: {job.responsibilities or ''}",
            f"Required Skills: {job.required_skills or ''}",
            f"Experience Required: {job.experience_years or 0} years",
            f"Education Level: {job.education_level or 'Not specified'}",
        ]
        
        return "\n".join(job_parts).strip()
    
    def extract_candidate_features(
        self,
        application_id: int,
        student: Student,
        resume: Optional[Resume],
        compute_embedding: bool = True
    ) -> CandidateFeatures:
        """
        Extract all features from a candidate.
        
        Args:
            application_id: Application ID
            student: Student object
            resume: Resume object (optional)
            compute_embedding: Whether to compute embedding (can skip if using cached)
            
        Returns:
            CandidateFeatures object
        """
        # Parse skills
        skills = self._parse_skills(student.skills)
        
        # Estimate experience
        experience_years = self._estimate_experience_years(student)
        
        # Build profile text
        profile_text = self._build_candidate_text(student, resume)
        
        # Generate embedding (optional)
        profile_embedding = None
        if compute_embedding:
            profile_embedding = self._generate_embedding(profile_text)
        
        # Alternatively, use pre-computed resume embedding if available
        if not profile_embedding and resume and resume.embedding_vector:
            try:
                profile_embedding = json.loads(resume.embedding_vector)
            except (json.JSONDecodeError, TypeError):
                # If parsing fails, compute fresh embedding
                profile_embedding = self._generate_embedding(profile_text)
        
        return CandidateFeatures(
            student_id=student.id,
            application_id=application_id,
            name=f"{student.first_name} {student.last_name}",
            skills=skills,
            experience_years=experience_years,
            education=f"{student.degree or ''} in {student.major or ''}",
            cgpa=student.cgpa,
            university=student.university,
            profile_embedding=profile_embedding,
            raw_profile_text=profile_text,
            resume_text=resume.raw_text if resume else None
        )
    
    def extract_job_features(self, job: Job) -> JobFeatures:
        """
        Extract all features from a job posting.
        
        **IMPORTANT:** This computes the job embedding ONCE.
        The caller should cache this result and reuse it for all candidates.
        
        Args:
            job: Job object
            
        Returns:
            JobFeatures object with precomputed embedding
        """
        # Parse required skills
        required_skills = self._parse_skills(job.required_skills)
        
        # Build job text
        job_text = self._build_job_text(job)
        
        # Generate embedding (computed ONCE per ranking execution)
        job_embedding = self._generate_embedding(job_text)
        
        return JobFeatures(
            job_id=job.id,
            title=job.title,
            required_skills=required_skills,
            required_experience_years=job.experience_years or 0,
            education_level=job.education_level,
            job_embedding=job_embedding,
            raw_job_text=job_text
        )
