"""
Matching Engine Module

Clean architecture for AI-powered candidate-job matching.

Components:
- feature_extractor: Extracts features from candidates and jobs
- scoring_engine: Implements the 40/40/20 scoring algorithm
- ranking_orchestrator: Orchestrates the end-to-end ranking process
"""

from app.matching.feature_extractor import FeatureExtractor, CandidateFeatures, JobFeatures
from app.matching.scoring_engine import ScoringEngine, ScoreBreakdown
from app.matching.ranking_orchestrator import RankingOrchestrator

__all__ = [
    "FeatureExtractor",
    "CandidateFeatures",
    "JobFeatures",
    "ScoringEngine",
    "ScoreBreakdown",
    "RankingOrchestrator",
]
