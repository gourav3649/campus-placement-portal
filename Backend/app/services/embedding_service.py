"""
Embedding generation service using sentence-transformers.
Generates and caches embeddings for text content.
Includes validation for data quality and consistency.
"""
import json
import logging
from typing import Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Expected embedding dimension (all-MiniLM-L6-v2)
EXPECTED_EMBEDDING_DIMENSION = 384

# Single model instance (lazy-loaded on first use)
_model_instance: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    """Get or initialize the embedding model (lazy loading)."""
    global _model_instance
    if _model_instance is None:
        logger.debug(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _model_instance = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info(f"Embedding model loaded successfully: {type(_model_instance).__name__}")
    return _model_instance


def generate_embedding(text: str) -> str:
    """
    Generate embedding for given text and return as JSON string.
    Validates embedding dimension and data quality.
    
    Args:
        text: Text to embed
        
    Returns:
        JSON-serialized embedding vector (list of floats)
        
    Raises:
        ValueError: If text is empty, extraction failed, or validation failed
    """
    # Validate input
    if not text or not isinstance(text, str):
        raise ValueError("Text must be a non-empty string")
    
    text = text.strip()
    if not text:
        raise ValueError("Cannot generate embedding from empty text after stripping")
    
    if len(text) < 5:
        raise ValueError(f"Text is too short ({len(text)} chars). Minimum 5 characters required.")
    
    try:
        model = get_embedding_model()
        
        # Normalize and truncate text if needed
        # Limit to 1000 chars to avoid memory issues
        text = text[:1000]
        
        # Generate embedding
        embedding = model.encode(text, convert_to_numpy=True)
        
        # Validate embedding dimension
        if embedding.shape[0] != EXPECTED_EMBEDDING_DIMENSION:
            raise ValueError(
                f"Invalid embedding dimension: got {embedding.shape[0]}, "
                f"expected {EXPECTED_EMBEDDING_DIMENSION}"
            )
        
        # Validate embedding is not all zeros
        if np.allclose(embedding, 0):
            raise ValueError("Generated embedding is all zeros (invalid embedding)")
        
        # Validate embedding values are finite (no NaN or Inf)
        if not np.all(np.isfinite(embedding)):
            raise ValueError("Embedding contains NaN or Inf values")
        
        # Convert to list and then JSON for storage
        embedding_list = embedding.tolist()
        
        # Validate list has correct length
        if len(embedding_list) != EXPECTED_EMBEDDING_DIMENSION:
            raise ValueError(
                f"Embedding list length mismatch after conversion: "
                f"got {len(embedding_list)}, expected {EXPECTED_EMBEDDING_DIMENSION}"
            )
        
        # Validate all values are floats
        if not all(isinstance(v, float) for v in embedding_list):
            raise ValueError("Not all embedding values are floats")
        
        embedding_json = json.dumps(embedding_list)
        
        logger.info(
            f"Embedding generated successfully. Text length: {len(text)}, "
            f"Embedding size: {len(embedding_list)} dims, JSON size: {len(embedding_json)} chars"
        )
        
        return embedding_json
        
    except ValueError as e:
        logger.error(f"Embedding validation failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during embedding generation: {str(e)}")
        raise ValueError(f"Failed to generate embedding: {str(e)}")


def embedding_from_json(json_str: str) -> np.ndarray:
    """
    Parse embedding from JSON string back to numpy array.
    Validates structure and dimension.
    
    Args:
        json_str: JSON-serialized embedding
        
    Returns:
        NumPy array of the embedding
        
    Raises:
        ValueError: If JSON is invalid or dimensions don't match
    """
    try:
        if not json_str or not isinstance(json_str, str):
            raise ValueError("Embedding JSON must be a non-empty string")
        
        embedding_list = json.loads(json_str)
        
        if not isinstance(embedding_list, list):
            raise ValueError("Embedding must be a JSON list")
        
        if len(embedding_list) != EXPECTED_EMBEDDING_DIMENSION:
            raise ValueError(
                f"Invalid embedding dimension: got {len(embedding_list)}, "
                f"expected {EXPECTED_EMBEDDING_DIMENSION}"
            )
        
        # Validate all values are numbers
        if not all(isinstance(v, (int, float)) for v in embedding_list):
            raise ValueError("Not all embedding values are numeric")
        
        embedding_array = np.array(embedding_list, dtype=np.float32)
        
        # Validate no NaN or Inf
        if not np.all(np.isfinite(embedding_array)):
            raise ValueError("Embedding contains NaN or Inf values")
        
        logger.debug(f"Embedding parsed successfully from JSON. Dimension: {len(embedding_list)}")
        return embedding_array
        
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse embedding from JSON: {str(e)}")
        raise ValueError(f"Invalid embedding JSON: {str(e)}")


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two embedding vectors.
    
    Args:
        vec1: First embedding vector
        vec2: Second embedding vector
        
    Returns:
        Cosine similarity score (0 to 1)
    """
    # Normalize vectors
    vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
    vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-8)
    
    # Compute dot product
    similarity = np.dot(vec1_norm, vec2_norm)
    
    # Clamp to [0, 1] range
    return float(max(0, min(1, similarity)))


def prepare_job_text_for_embedding(job) -> str:
    """
    Prepare job description for embedding by combining relevant fields.
    Validates that job has meaningful content.
    
    Args:
        job: Job model instance
        
    Returns:
        Combined text for embedding
        
    Raises:
        ValueError: If job has no content to embed
    """
    parts = []
    
    if job.title and isinstance(job.title, str) and job.title.strip():
        parts.append(f"Job Title: {job.title.strip()}")
    if job.description and isinstance(job.description, str) and job.description.strip():
        parts.append(f"Description: {job.description.strip()}")
    if hasattr(job, 'required_skills') and job.required_skills and isinstance(job.required_skills, str) and job.required_skills.strip():
        parts.append(f"Required Skills: {job.required_skills.strip()}")
    if hasattr(job, 'requirements') and job.requirements and isinstance(job.requirements, str) and job.requirements.strip():
        parts.append(f"Requirements: {job.requirements.strip()}")
    if hasattr(job, 'responsibilities') and job.responsibilities and isinstance(job.responsibilities, str) and job.responsibilities.strip():
        parts.append(f"Responsibilities: {job.responsibilities.strip()}")
    
    if not parts:
        raise ValueError(
            "Job has no content to embed. At least one of: "
            "title, description, required_skills, requirements, or responsibilities is required."
        )
    
    combined_text = " ".join(parts)
    logger.debug(f"Job text prepared for embedding: {len(combined_text)} chars from {len(parts)} fields")
    return combined_text


def prepare_resume_text_for_embedding(raw_text: str) -> str:
    """
    Prepare resume text for embedding (already extracted, just normalize).
    Validates text is suitable for embedding.
    
    Args:
        raw_text: Raw extracted resume text
        
    Returns:
        Normalized text for embedding
        
    Raises:
        ValueError: If raw_text is empty or too short
    """
    if not raw_text or not isinstance(raw_text, str):
        raise ValueError("Resume text must be a non-empty string")
    
    # Basic normalization
    text = raw_text.strip()
    # Remove excessive whitespace
    text = " ".join(text.split())
    
    if not text:
        raise ValueError("Resume text is empty after normalization")
    
    if len(text) < 10:
        raise ValueError(f"Resume text too short ({len(text)} chars). Minimum 10 characters required.")
    
    logger.debug(f"Resume text prepared for embedding: {len(text)} chars (normalized from {len(raw_text)})")
    return text
