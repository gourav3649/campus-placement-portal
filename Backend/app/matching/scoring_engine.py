"""
Scoring Engine Module

Implements the 40/40/20 matching algorithm:
- 40% Semantic similarity (embedding-based)
- 40% Skills match (Jaccard + semantic)
- 20% Experience match

Accepts precomputed embeddings to avoid redundant computation.
"""

import numpy as np
from dataclasses import dataclass
from typing import List
from sklearn.metrics.pairwise import cosine_similarity

from app.matching.feature_extractor import CandidateFeatures, JobFeatures


@dataclass
class ScoreBreakdown:
    """Structured score breakdown for transparency."""
    overall_score: float
    semantic_score: float
    skills_score: float
    experience_score: float
    
    def to_dict(self):
        """Convert to dictionary for database storage."""
        return {
            "match_score": round(self.overall_score, 2),
            "semantic_similarity": round(self.semantic_score, 2),
            "skills_match_score": round(self.skills_score, 2),
            "experience_match_score": round(self.experience_score, 2)
        }


class ScoringEngine:
    """
    Implements the 40/40/20 scoring algorithm.
    
    All methods accept precomputed features to ensure:
    - No redundant embedding generation
    - Job embedding computed only once
    - Candidate embeddings reused from cache when available
    """
    
    def calculate_semantic_similarity(
        self,
        job_embedding: List[float],
        candidate_embedding: List[float]
    ) -> float:
        """
        Calculate cosine similarity between job and candidate embeddings.
        
        Args:
            job_embedding: Precomputed job embedding vector
            candidate_embedding: Precomputed candidate embedding vector
            
        Returns:
            Similarity score (0-1)
        """
        if not job_embedding or not candidate_embedding:
            return 0.0
        
        # Convert to numpy arrays
        vec1 = np.array(job_embedding).reshape(1, -1)
        vec2 = np.array(candidate_embedding).reshape(1, -1)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(vec1, vec2)[0][0]
        
        return float(max(0.0, min(1.0, similarity)))  # Clamp to [0, 1]
    
    def calculate_skills_match(
        self,
        job_skills: List[str],
        candidate_skills: List[str]
    ) -> float:
        """
        Calculate skills match using Jaccard similarity.
        
        Combines:
        - 40% Jaccard (exact match)
        - 60% Semantic similarity of skill text
        
        Args:
            job_skills: List of required skills
            candidate_skills: List of candidate's skills
            
        Returns:
            Skills match score (0-100)
        """
        if not job_skills:
            return 100.0  # No skills required = perfect match
        
        if not candidate_skills:
            return 0.0  # No skills provided = no match
        
        # Normalize for case-insensitive comparison
        job_skill_set = set([s.lower() for s in job_skills])
        candidate_skill_set = set([s.lower() for s in candidate_skills])
        
        # Calculate Jaccard similarity
        intersection = job_skill_set.intersection(candidate_skill_set)
        union = job_skill_set.union(candidate_skill_set)
        
        jaccard_score = len(intersection) / len(union) if union else 0.0
        
        # Calculate semantic similarity of skills text
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        
        job_skills_text = ' '.join(job_skill_set)
        candidate_skills_text = ' '.join(candidate_skill_set)
        
        job_skills_embedding = model.encode(job_skills_text, convert_to_numpy=True).reshape(1, -1)
        candidate_skills_embedding = model.encode(candidate_skills_text, convert_to_numpy=True).reshape(1, -1)
        
        semantic_score = cosine_similarity(job_skills_embedding, candidate_skills_embedding)[0][0]
        semantic_score = max(0.0, min(1.0, semantic_score))
        
        # Combined score (weighted average)
        combined_score = (jaccard_score * 0.4 + semantic_score * 0.6) * 100
        
        return min(100.0, combined_score)
    
    def calculate_experience_match(
        self,
        required_years: int,
        candidate_years: float
    ) -> float:
        """
        Calculate experience match score.
        
        Args:
            required_years: Required years of experience
            candidate_years: Candidate's years of experience
            
        Returns:
            Experience match score (0-100)
        """
        if required_years <= 0:
            return 100.0  # No experience required
        
        if candidate_years >= required_years:
            return 100.0  # Meets or exceeds requirement
        
        # Linear score for partial experience
        score = (candidate_years / required_years) * 100
        
        return min(100.0, max(0.0, score))
    
    def calculate_overall_score(
        self,
        semantic_similarity: float,
        skills_score: float,
        experience_score: float
    ) -> float:
        """
        Calculate weighted overall score using 40/40/20 formula.
        
        Formula:
        overall = (semantic * 0.4 + skills * 0.4 + experience * 0.2) * 100
        
        Args:
            semantic_similarity: Semantic similarity (0-1)
            skills_score: Skills match score (0-100)
            experience_score: Experience match score (0-100)
            
        Returns:
            Overall match score (0-100)
        """
        overall = (
            semantic_similarity * 0.4 +        # 40% semantic
            (skills_score / 100) * 0.4 +       # 40% skills
            (experience_score / 100) * 0.2     # 20% experience
        ) * 100
        
        return min(100.0, max(0.0, overall))
    
    def score_candidate(
        self,
        job_features: JobFeatures,
        candidate_features: CandidateFeatures
    ) -> ScoreBreakdown:
        """
        Calculate comprehensive match score for a candidate-job pair.
        
        **Efficient Design:**
        - Accepts precomputed job embedding (computed once for all candidates)
        - Uses cached candidate embedding when available
        - No redundant computation
        
        Args:
            job_features: Precomputed job features (with embedding)
            candidate_features: Precomputed candidate features (with embedding)
            
        Returns:
            ScoreBreakdown with all component scores
        """
        # Calculate semantic similarity (using precomputed embeddings)
        semantic_similarity = self.calculate_semantic_similarity(
            job_features.job_embedding,
            candidate_features.profile_embedding
        )
        
        # Calculate skills match
        skills_score = self.calculate_skills_match(
            job_features.required_skills,
            candidate_features.skills
        )
        
        # Calculate experience match
        experience_score = self.calculate_experience_match(
            job_features.required_experience_years,
            candidate_features.experience_years
        )
        
        # Calculate overall score (40/40/20 weighted)
        overall_score = self.calculate_overall_score(
            semantic_similarity,
            skills_score,
            experience_score
        )
        
        return ScoreBreakdown(
            overall_score=overall_score,
            semantic_score=semantic_similarity * 100,  # Convert to 0-100
            skills_score=skills_score,
            experience_score=experience_score
        )
