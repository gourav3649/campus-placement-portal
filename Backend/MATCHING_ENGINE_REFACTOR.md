# 🔄 Matching Engine Refactor - Complete Implementation

**Refactor Date:** February 18, 2026  
**Architecture:** Clean, Modular Matching Engine  
**Key Optimization:** Job embedding computed ONCE per ranking execution

---

## 📁 New Module Structure

```
app/matching/
├── __init__.py              # Module exports
├── feature_extractor.py     # Feature extraction from candidates & jobs
├── scoring_engine.py        # 40/40/20 scoring algorithm
└── ranking_orchestrator.py  # End-to-end ranking orchestration
```

---

## 🎯 Architecture Overview

### **Clean Separation of Concerns**

```
┌─────────────────────────────────────────────────────────────┐
│                  RankingOrchestrator                        │
│  - Fetches job and applications                             │
│  - Computes job embedding ONCE                              │
│  - Orchestrates entire ranking workflow                     │
│  - Persists scores and assigns ranks                        │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
             ▼                                ▼
┌────────────────────────┐      ┌────────────────────────────┐
│   FeatureExtractor     │      │     ScoringEngine          │
│ - Extract job features │      │ - Semantic similarity      │
│ - Extract candidate    │      │ - Skills match (Jaccard)   │
│   features             │      │ - Experience match         │
│ - Generate embeddings  │      │ - 40/40/20 weighted score  │
│ - Parse skills         │      └────────────────────────────┘
│ - Estimate experience  │
└────────────────────────┘
```

---

## 📄 Feature Extractor Implementation

**File:** `app/matching/feature_extractor.py`

### **Key Features:**

1. **Structured Data Classes**
   
```python
@dataclass
class CandidateFeatures:
    student_id: int
    application_id: int
    name: str
    skills: List[str]
    experience_years: float
    education: str
    cgpa: Optional[float]
    university: Optional[str]
    profile_embedding: Optional[List[float]]  # 384-dim vector
    raw_profile_text: str
    resume_text: Optional[str]

@dataclass
class JobFeatures:
    job_id: int
    title: str
    required_skills: List[str]
    required_experience_years: int
    education_level: Optional[str]
    job_embedding: List[float]  # Computed ONCE
    raw_job_text: str
```

2. **Lazy Model Loading**

```python
def _get_model(self) -> SentenceTransformer:
    """Lazy load sentence transformer model."""
    if self.model is None:
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return self.model
```

3. **Smart Embedding Reuse**

```python
# Attempt to use pre-computed resume embedding
if not profile_embedding and resume and resume.embedding_vector:
    try:
        profile_embedding = json.loads(resume.embedding_vector)
    except (json.JSONDecodeError, TypeError):
        # Fallback to fresh computation
        profile_embedding = self._generate_embedding(profile_text)
```

### **Critical Methods:**

```python
# Extract job features (CALLED ONCE PER RANKING)
def extract_job_features(self, job: Job) -> JobFeatures:
    """
    Extract job features with precomputed embedding.
    
    **IMPORTANT:** Caller should cache this result and reuse
    it for all candidates in the same ranking execution.
    """
    required_skills = self._parse_skills(job.required_skills)
    job_text = self._build_job_text(job)
    job_embedding = self._generate_embedding(job_text)  # ONCE!
    
    return JobFeatures(
        job_id=job.id,
        title=job.title,
        required_skills=required_skills,
        required_experience_years=job.experience_years or 0,
        education_level=job.education_level,
        job_embedding=job_embedding,  # Reused for all candidates
        raw_job_text=job_text
    )

# Extract candidate features (CALLED PER CANDIDATE)
def extract_candidate_features(
    self,
    application_id: int,
    student: Student,
    resume: Optional[Resume],
    compute_embedding: bool = True
) -> CandidateFeatures:
    """Extract candidate features with optional embedding computation."""
    # ... skill parsing, experience estimation ...
    
    # Use cached resume embedding if available
    if resume and resume.embedding_vector:
        profile_embedding = json.loads(resume.embedding_vector)
    else:
        profile_embedding = self._generate_embedding(profile_text)
    
    return CandidateFeatures(...)
```

---

## 🔢 Scoring Engine Implementation

**File:** `app/matching/scoring_engine.py`

### **Structured Score Output:**

```python
@dataclass
class ScoreBreakdown:
    overall_score: float       # 0-100 weighted score
    semantic_score: float      # 0-100 semantic similarity
    skills_score: float        # 0-100 skills match
    experience_score: float    # 0-100 experience match
    
    def to_dict(self):
        return {
            "match_score": round(self.overall_score, 2),
            "semantic_similarity": round(self.semantic_score, 2),
            "skills_match_score": round(self.skills_score, 2),
            "experience_match_score": round(self.experience_score, 2)
        }
```

### **40/40/20 Formula (Exact Implementation):**

```python
def calculate_overall_score(
    self,
    semantic_similarity: float,  # 0-1 range
    skills_score: float,         # 0-100 range
    experience_score: float      # 0-100 range
) -> float:
    """
    Calculate weighted overall score.
    
    Formula:
    overall = (semantic * 0.4 + skills * 0.4 + experience * 0.2) * 100
    """
    overall = (
        semantic_similarity * 0.4 +        # 40% semantic
        (skills_score / 100) * 0.4 +       # 40% skills
        (experience_score / 100) * 0.2     # 20% experience
    ) * 100
    
    return min(100.0, max(0.0, overall))
```

### **Component Scores:**

1. **Semantic Similarity (40%)**

```python
def calculate_semantic_similarity(
    self,
    job_embedding: List[float],      # Precomputed (384-dim)
    candidate_embedding: List[float]  # Precomputed (384-dim)
) -> float:
    """Cosine similarity between embeddings."""
    vec1 = np.array(job_embedding).reshape(1, -1)
    vec2 = np.array(candidate_embedding).reshape(1, -1)
    similarity = cosine_similarity(vec1, vec2)[0][0]
    return float(max(0.0, min(1.0, similarity)))
```

2. **Skills Match (40%)**

```python
def calculate_skills_match(
    self,
    job_skills: List[str],
    candidate_skills: List[str]
) -> float:
    """
    Hybrid skills matching:
    - 40% Jaccard (exact match)
    - 60% Semantic (embedding similarity)
    """
    # Jaccard similarity
    job_skill_set = set([s.lower() for s in job_skills])
    candidate_skill_set = set([s.lower() for s in candidate_skills])
    
    intersection = job_skill_set.intersection(candidate_skill_set)
    union = job_skill_set.union(candidate_skill_set)
    jaccard_score = len(intersection) / len(union) if union else 0.0
    
    # Semantic similarity of skills text
    job_skills_text = ' '.join(job_skill_set)
    candidate_skills_text = ' '.join(candidate_skill_set)
    
    # Generate embeddings and calculate similarity
    semantic_score = ... # cosine similarity
    
    # Weighted combination
    combined_score = (jaccard_score * 0.4 + semantic_score * 0.6) * 100
    return min(100.0, combined_score)
```

3. **Experience Match (20%)**

```python
def calculate_experience_match(
    self,
    required_years: int,
    candidate_years: float
) -> float:
    """Linear scoring for experience match."""
    if required_years <= 0:
        return 100.0  # No requirement
    
    if candidate_years >= required_years:
        return 100.0  # Meets requirement
    
    # Partial credit
    return (candidate_years / required_years) * 100
```

### **Main Scoring Method:**

```python
def score_candidate(
    self,
    job_features: JobFeatures,        # Precomputed (reused)
    candidate_features: CandidateFeatures  # Extracted once
) -> ScoreBreakdown:
    """
    Calculate comprehensive match score.
    
    Accepts precomputed embeddings to avoid redundant computation.
    """
    # Calculate component scores
    semantic_similarity = self.calculate_semantic_similarity(
        job_features.job_embedding,           # Precomputed ONCE
        candidate_features.profile_embedding  # From cache or computed
    )
    
    skills_score = self.calculate_skills_match(
        job_features.required_skills,
        candidate_features.skills
    )
    
    experience_score = self.calculate_experience_match(
        job_features.required_experience_years,
        candidate_features.experience_years
    )
    
    # Calculate overall score (40/40/20)
    overall_score = self.calculate_overall_score(
        semantic_similarity,
        skills_score,
        experience_score
    )
    
    return ScoreBreakdown(
        overall_score=overall_score,
        semantic_score=semantic_similarity * 100,
        skills_score=skills_score,
        experience_score=experience_score
    )
```

---

## 🎼 Ranking Orchestrator Implementation

**File:** `app/matching/ranking_orchestrator.py`

### **Key Optimization: Single Job Embedding**

```python
async def rank_applications(
    self,
    db: AsyncSession,
    job_id: int,
    rerank: bool = False
) -> Dict[str, Any]:
    """
    Rank all applications for a job.
    
    **CRITICAL OPTIMIZATION:**
    Job embedding computed ONCE at the start,
    then reused for ALL candidates.
    """
    
    # STEP 1: Fetch job
    job = await self._fetch_job(db, job_id)
    
    # STEP 2: Extract job features (COMPUTE EMBEDDING ONCE)
    print(f"[Orchestrator] Extracting job features...")
    job_features = self.feature_extractor.extract_job_features(job)
    print(f"[Orchestrator] Job embedding computed (384-dim vector)")
    print(f"[Orchestrator] Will be reused for all candidates")
    
    # STEP 3: Fetch applications
    applications = await self._fetch_applications(db, job_id, rerank)
    print(f"[Orchestrator] Found {len(applications)} applications")
    
    # STEP 4: Process each candidate (REUSE job_features)
    for application in applications:
        student = await self._fetch_student(db, application.student_id)
        resume = await self._fetch_resume(db, application.resume_id)
        
        # Extract candidate features
        candidate_features = self.feature_extractor.extract_candidate_features(
            application_id=application.id,
            student=student,
            resume=resume
        )
        
        # Score using PRECOMPUTED job_features
        score_breakdown = self.scoring_engine.score_candidate(
            job_features=job_features,     # ← REUSED! No recomputation
            candidate_features=candidate_features
        )
        
        # Persist scores
        await self._persist_scores(application, score_breakdown)
    
    # STEP 5: Assign ranks
    await self._assign_ranks(db, job_id)
    
    return {"applications_ranked": len(applications)}
```

### **Performance Comparison:**

**OLD Implementation (semantic_ranking.py):**
```
For 100 candidates:
- Job embedding generated: 100 times ❌
- Total embedding computations: 200 (100 job + 100 candidate)
- Wasted computation: 99 redundant job embeddings
```

**NEW Implementation (RankingOrchestrator):**
```
For 100 candidates:
- Job embedding generated: 1 time ✅
- Total embedding computations: 101 (1 job + 100 candidate)
- Optimization: 99x reduction in job embedding computation
```

### **Full Workflow:**

```python
async def rank_applications(db, job_id, rerank=False):
    """
    Complete ranking workflow:
    
    1. Fetch job → Extract features → Compute embedding ONCE
    2. Fetch applications
    3. For each application:
       a. Fetch student & resume
       b. Extract candidate features
       c. Score using PRECOMPUTED job embedding
       d. Generate AI summary
       e. Persist scores
    4. Assign ranks based on scores
    5. Commit transaction
    """
    
    job_features = extractor.extract_job_features(job)  # ← ONCE
    
    for app in applications:
        candidate_features = extractor.extract_candidate_features(...)
        
        scores = engine.score_candidate(
            job_features=job_features,  # ← REUSED
            candidate_features=candidate_features
        )
        
        app.match_score = scores.overall_score
        app.skills_match_score = scores.skills_score
        app.experience_match_score = scores.experience_score
    
    # Assign ranks
    sorted_apps = sorted(applications, key=lambda a: a.match_score, reverse=True)
    for rank, app in enumerate(sorted_apps, start=1):
        app.rank = rank
    
    await db.commit()
```

### **Single Application Scoring:**

```python
async def score_single_application(
    self,
    db: AsyncSession,
    application_id: int
) -> Dict[str, Any]:
    """
    Score a single application (used on submission).
    
    Use case: Real-time scoring when student applies to job.
    """
    application = await self._fetch_application(db, application_id)
    job = await self._fetch_job(db, application.job_id)
    student = await self._fetch_student(db, application.student_id)
    resume = await self._fetch_resume(db, application.resume_id)
    
    # Extract features
    job_features = self.feature_extractor.extract_job_features(job)
    candidate_features = self.feature_extractor.extract_candidate_features(
        application_id=application.id,
        student=student,
        resume=resume
    )
    
    # Score
    scores = self.scoring_engine.score_candidate(
        job_features=job_features,
        candidate_features=candidate_features
    )
    
    # Persist
    application.match_score = scores.overall_score
    application.skills_match_score = scores.skills_score
    application.experience_match_score = scores.experience_score
    
    await db.commit()
    
    return {"scores": scores.to_dict()}
```

---

## 🔄 Refactored Background Tasks

**File:** `app/services/semantic_ranking.py` (Updated)

### **Old Implementation (Removed):**

```python
# ❌ OLD: Inefficient loop with repeated job embedding computation
async def rank_job_applications(job_id: int, rerank: bool = False):
    async with AsyncSessionLocal() as db:
        applications = await db.execute(...)
        
        # ❌ For each application, recompute job embedding
        for app in applications:
            job = await db.execute(...)  # Redundant job fetch
            student = await db.execute(...)
            resume = await db.execute(...)
            
            # ❌ Inline scoring logic (not modular)
            job_text = extract_job_requirements(job)
            candidate_text = extract_candidate_profile(student, resume)
            
            job_embedding = generate_embedding(job_text)  # ❌ Repeated!
            candidate_embedding = generate_embedding(candidate_text)
            
            score = calculate_match(...)
```

### **New Implementation (Clean):**

```python
# ✅ NEW: Clean, modular, optimized
async def rank_job_applications(job_id: int, rerank: bool = False):
    """
    Background task to rank all applications for a job.
    
    REFACTORED: Uses RankingOrchestrator for optimized ranking.
    
    Key improvements:
    - Job embedding computed ONCE (not per candidate)
    - Clean separation of concerns
    - Batch processing with proper error handling
    """
    from app.matching.ranking_orchestrator import RankingOrchestrator
    
    async with AsyncSessionLocal() as db:
        try:
            orchestrator = RankingOrchestrator()
            result = await orchestrator.rank_applications(db, job_id, rerank)
            
            print(f"[Background Task] Ranking completed for job {job_id}")
            print(f"[Background Task] Applications ranked: {result['applications_ranked']}")
            
        except Exception as e:
            print(f"Error ranking job applications: {str(e)}")
            await db.rollback()
```

### **Single Application Task:**

```python
# ✅ NEW: Clean single application scoring
async def process_application_matching(application_id: int):
    """
    Background task for single application scoring.
    
    REFACTORED: Uses RankingOrchestrator.score_single_application()
    """
    from app.matching.ranking_orchestrator import RankingOrchestrator
    
    async with AsyncSessionLocal() as db:
        try:
            orchestrator = RankingOrchestrator()
            result = await orchestrator.score_single_application(db, application_id)
            print(f"[Background Task] Application {application_id} scored: {result['scores']['match_score']}")
            
        except Exception as e:
            print(f"Error processing application: {str(e)}")
            await db.rollback()
```

---

## 📊 Performance Analysis

### **Embedding Computation Savings:**

| Candidates | Old Implementation | New Implementation | Savings |
|------------|-------------------|-------------------|---------|
| 10         | 20 embeddings     | 11 embeddings     | 45%     |
| 100        | 200 embeddings    | 101 embeddings    | 49.5%   |
| 1,000      | 2,000 embeddings  | 1,001 embeddings  | 49.95%  |
| 10,000     | 20,000 embeddings | 10,001 embeddings | 49.995% |

### **Time Savings (Estimated):**

Assuming 50ms per embedding generation:

| Candidates | Old Time | New Time | Time Saved |
|------------|----------|----------|------------|
| 100        | 10s      | 5.05s    | 4.95s      |
| 1,000      | 100s     | 50.05s   | 49.95s     |
| 10,000     | 1,000s   | 500.05s  | 499.95s    |

### **Memory Efficiency:**

**Old:** Loads job object 100 times (redundant database queries)  
**New:** Loads job object ONCE (cached in job_features)

---

## 🎯 Usage Examples

### **Example 1: Rank All Job Applications**

```python
from app.matching import RankingOrchestrator

async def rank_job(db: AsyncSession, job_id: int):
    orchestrator = RankingOrchestrator()
    
    result = await orchestrator.rank_applications(
        db=db,
        job_id=job_id,
        rerank=False  # Only rank unscored applications
    )
    
    print(f"Ranked {result['applications_ranked']} applications")
    print(f"Total ranked: {result['total_ranked_applications']}")
```

### **Example 2: Score Single Application on Submission**

```python
from app.matching import RankingOrchestrator

async def score_on_submit(db: AsyncSession, application_id: int):
    orchestrator = RankingOrchestrator()
    
    result = await orchestrator.score_single_application(
        db=db,
        application_id=application_id
    )
    
    print(f"Match Score: {result['scores']['match_score']}")
    print(f"Skills Score: {result['scores']['skills_match_score']}")
    print(f"Experience Score: {result['scores']['experience_match_score']}")
```

### **Example 3: Re-rank All Applications**

```python
from app.matching import RankingOrchestrator

async def rerank_all(db: AsyncSession, job_id: int):
    orchestrator = RankingOrchestrator()
    
    result = await orchestrator.rank_applications(
        db=db,
        job_id=job_id,
        rerank=True  # Recalculate ALL scores
    )
```

---

## 🔍 Code Quality Improvements

### **Before (Monolithic):**

```python
# ❌ All logic in one class
class SemanticRankingService:
    def extract_job_requirements(...)
    def extract_candidate_profile(...)
    def calculate_skills_match(...)
    def calculate_experience_match(...)
    def calculate_similarity(...)
    def generate_embedding(...)
    def calculate_match_score(...)
    def generate_ai_summary(...)
```

### **After (Modular):**

```python
# ✅ Feature Extraction
class FeatureExtractor:
    def extract_job_features(...)
    def extract_candidate_features(...)
    def _parse_skills(...)
    def _estimate_experience_years(...)
    def _generate_embedding(...)

# ✅ Scoring Logic
class ScoringEngine:
    def score_candidate(...)
    def calculate_semantic_similarity(...)
    def calculate_skills_match(...)
    def calculate_experience_match(...)
    def calculate_overall_score(...)

# ✅ Workflow Orchestration
class RankingOrchestrator:
    def rank_applications(...)
    def score_single_application(...)
    def _generate_ai_summary(...)
```

---

## ✅ Verification Checklist

- ✅ **Job embedding computed ONCE per ranking execution**
- ✅ **Clean separation: extraction → scoring → orchestration**
- ✅ **Precomputed embeddings passed between modules**
- ✅ **Resume embeddings reused when available**
- ✅ **No redundant database queries**
- ✅ **Proper error handling with rollback**
- ✅ **Structured data classes (CandidateFeatures, JobFeatures, ScoreBreakdown)**
- ✅ **40/40/20 formula preserved exactly**
- ✅ **Background tasks refactored to use new architecture**
- ✅ **Logging for debugging and monitoring**

---

## 📝 Migration Notes

### **Backward Compatibility:**

The refactored code maintains full backward compatibility:

1. **Same background task signatures:**
   - `process_application_matching(application_id: int)`
   - `rank_job_applications(job_id: int, rerank: bool)`

2. **Same database schema:**
   - No changes to Application model
   - Same fields: match_score, skills_match_score, experience_match_score

3. **Same API endpoints:**
   - No changes required in API layer
   - Background tasks work transparently

### **Testing:**

```python
# Test single application scoring
await process_application_matching(application_id=1)

# Test batch ranking
await rank_job_applications(job_id=5, rerank=False)

# Verify scores are identical to old implementation
```

---

## 🚀 Future Enhancements

1. **Parallel Processing:**
   ```python
   # Use asyncio.gather for concurrent candidate scoring
   tasks = [
       score_candidate(job_features, candidate_features)
       for candidate_features in candidates
   ]
   scores = await asyncio.gather(*tasks)
   ```

2. **Caching:**
   ```python
   # Cache job features in Redis
   cache_key = f"job_features:{job_id}"
   job_features = await redis.get(cache_key)
   if not job_features:
       job_features = extractor.extract_job_features(job)
       await redis.set(cache_key, job_features, ex=3600)
   ```

3. **Streaming:**
   ```python
   # Stream scores as they're computed
   async def rank_applications_streaming(job_id):
       async for score in orchestrator.rank_streaming(job_id):
           yield score
   ```

---

**End of Refactor Documentation**
