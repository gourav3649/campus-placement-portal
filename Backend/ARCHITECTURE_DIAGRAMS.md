# Matching Engine Architecture - Visual Diagrams

## 🏗️ High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         API Layer                                  │
│  ┌──────────────────┐              ┌──────────────────┐            │
│  │  POST /jobs/{id} │              │ POST /applications│            │
│  │      /rank       │              │                   │            │
│  └────────┬─────────┘              └─────────┬─────────┘            │
└───────────┼──────────────────────────────────┼────────────────────┘
            │                                   │
            │ BackgroundTasks.add_task()        │ BackgroundTasks.add_task()
            ▼                                   ▼
┌───────────────────────────────────────────────────────────────────┐
│                   Background Task Layer                            │
│  ┌────────────────────────────────┐  ┌──────────────────────────┐ │
│  │ rank_job_applications()        │  │ process_application_     │ │
│  │ (job_id, rerank)               │  │ matching(application_id) │ │
│  └────────────────┬───────────────┘  └──────────┬───────────────┘ │
└───────────────────┼──────────────────────────────┼─────────────────┘
                    │                               │
                    │ Uses                          │ Uses
                    ▼                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Matching Engine Module                           │
│                     (app/matching/)                                 │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │          RankingOrchestrator                                │   │
│  │  ┌────────────────────────────────────────────────────┐     │   │
│  │  │  rank_applications(db, job_id, rerank)            │     │   │
│  │  │  score_single_application(db, application_id)     │     │   │
│  │  └────────────────────────────────────────────────────┘     │   │
│  │           │                                 │                │   │
│  │           │ Uses                            │ Uses           │   │
│  │           ▼                                 ▼                │   │
│  │  ┌──────────────────┐            ┌──────────────────┐       │   │
│  │  │ FeatureExtractor │            │  ScoringEngine   │       │   │
│  │  ├──────────────────┤            ├──────────────────┤       │   │
│  │  │ extract_job_     │            │ score_candidate()│       │   │
│  │  │   features()     │            │ calculate_       │       │   │
│  │  │ extract_         │            │   semantic_      │       │   │
│  │  │   candidate_     │            │   similarity()   │       │   │
│  │  │   features()     │            │ calculate_       │       │   │
│  │  │                  │            │   skills_match() │       │   │
│  │  │ _generate_       │            │ calculate_       │       │   │
│  │  │   embedding()    │            │   experience_    │       │   │
│  │  │ _parse_skills()  │            │   match()        │       │   │
│  │  └──────────────────┘            └──────────────────┘       │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                    │                               │
                    │ Reads/Writes                  │
                    ▼                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Database Layer                                 │
│  ┌──────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐           │
│  │   Job    │  │ Student │  │ Resume  │  │ Application │           │
│  └──────────┘  └─────────┘  └─────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow - Batch Ranking

```
Step 1: Trigger Ranking
┌─────────────┐
│  Recruiter  │ POST /jobs/5/rank
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│ API: trigger_ai_ranking()       │
│ background_tasks.add_task(      │
│   rank_job_applications, 5      │
│ )                               │
└──────┬──────────────────────────┘
       │
       ▼

Step 2: Background Task Execution
┌─────────────────────────────────────────┐
│ rank_job_applications(job_id=5)        │
│   ↓                                     │
│   RankingOrchestrator()                 │
│   orchestrator.rank_applications(       │
│     db, job_id=5, rerank=False          │
│   )                                     │
└──────┬──────────────────────────────────┘
       │
       ▼

Step 3: RankingOrchestrator.rank_applications()
┌─────────────────────────────────────────────────────────┐
│ 1. Fetch Job (id=5)                                     │
│    ↓                                                    │
│ 2. FeatureExtractor.extract_job_features(job)          │
│    ↓                                                    │
│    • Parse required_skills: ["Python", "FastAPI"]      │
│    • Build job_text: "Backend Developer..."            │
│    • **Generate job_embedding (384-dim) ONCE** ✓       │
│    ↓                                                    │
│    Returns: JobFeatures(                                │
│      job_id=5,                                          │
│      required_skills=["Python", "FastAPI"],             │
│      job_embedding=[0.23, 0.45, ...],  # 384 dims      │
│      ...                                                │
│    )                                                    │
│    ↓                                                    │
│ 3. Fetch Applications for job_id=5                     │
│    ↓                                                    │
│    Result: [app_10, app_11, app_12, ..., app_109]     │
│    (100 applications)                                   │
│    ↓                                                    │
│ 4. FOR EACH APPLICATION (loop 100 times):              │
│    ┌─────────────────────────────────────────────┐     │
│    │ app_10:                                     │     │
│    │   a. Fetch Student (id=20)                  │     │
│    │   b. Fetch Resume (id=15)                   │     │
│    │   c. FeatureExtractor.extract_candidate_    │     │
│    │      features(app_10, student, resume)      │     │
│    │      ↓                                       │     │
│    │      • Parse skills: ["Python", "React"]    │     │
│    │      • Estimate experience: 2.5 years       │     │
│    │      • Load resume.embedding_vector (cache) │     │
│    │        OR generate fresh embedding          │     │
│    │      ↓                                       │     │
│    │      Returns: CandidateFeatures(            │     │
│    │        application_id=10,                   │     │
│    │        skills=["Python", "React"],          │     │
│    │        experience_years=2.5,                │     │
│    │        profile_embedding=[0.18, 0.52, ...], │     │
│    │        ...                                   │     │
│    │      )                                       │     │
│    │   d. ScoringEngine.score_candidate(         │     │
│    │        job_features,      # ← REUSED!       │     │
│    │        candidate_features                   │     │
│    │      )                                       │     │
│    │      ↓                                       │     │
│    │      • Semantic: cosine_similarity(         │     │
│    │          job_features.job_embedding,        │     │
│    │          candidate_features.profile_        │     │
│    │            embedding                         │     │
│    │        ) = 0.823                             │     │
│    │      • Skills: Jaccard + semantic = 75.0    │     │
│    │      • Experience: 2.5/2 * 100 = 100.0      │     │
│    │      • Overall: (0.823*0.4 + 0.75*0.4 +     │     │
│    │                  1.0*0.2) * 100 = 82.92     │     │
│    │      ↓                                       │     │
│    │      Returns: ScoreBreakdown(               │     │
│    │        overall_score=82.92,                 │     │
│    │        semantic_score=82.3,                 │     │
│    │        skills_score=75.0,                   │     │
│    │        experience_score=100.0               │     │
│    │      )                                       │     │
│    │   e. Update Application:                    │     │
│    │      app_10.match_score = 82.92             │     │
│    │      app_10.skills_match_score = 75.0       │     │
│    │      app_10.experience_match_score = 100.0  │     │
│    └─────────────────────────────────────────────┘     │
│    ┌─────────────────────────────────────────────┐     │
│    │ app_11: (same process, REUSE job_features)  │     │
│    └─────────────────────────────────────────────┘     │
│    ┌─────────────────────────────────────────────┐     │
│    │ app_12: (same process, REUSE job_features)  │     │
│    └─────────────────────────────────────────────┘     │
│    ...                                                  │
│    (98 more applications)                               │
│    ↓                                                    │
│ 5. Commit all scores to database                       │
│    ↓                                                    │
│ 6. Fetch all ranked applications, sort by match_score  │
│    ↓                                                    │
│ 7. Assign ranks:                                       │
│    app_10.rank = 1  (score: 92.5)                      │
│    app_15.rank = 2  (score: 88.3)                      │
│    app_12.rank = 3  (score: 82.92)                     │
│    ...                                                  │
│    ↓                                                    │
│ 8. Commit ranks                                        │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Return:                 │
│ {                       │
│   "applications_ranked":│
│     100,                │
│   "total_ranked":       │
│     100,                │
│   "message": "Success"  │
│ }                       │
└─────────────────────────┘
```

---

## 💡 Key Optimization - Job Embedding Reuse

```
OLD APPROACH (Inefficient):
┌─────────────────────────────────────────────────────┐
│ For each of 100 candidates:                         │
│   1. Generate job_embedding         ← 100 times! ❌ │
│   2. Generate candidate_embedding   ← 100 times     │
│   3. Calculate similarity                           │
│   4. Calculate scores                               │
└─────────────────────────────────────────────────────┘
Total embeddings: 200 (100 job + 100 candidate)
Wasted computation: 99 redundant job embeddings


NEW APPROACH (Optimized):
┌─────────────────────────────────────────────────────┐
│ Before loop:                                         │
│   1. Generate job_embedding ONCE    ← 1 time! ✓    │
│                                                      │
│ For each of 100 candidates:                         │
│   2. Generate candidate_embedding   ← 100 times     │
│   3. Calculate similarity (REUSE job_embedding)     │
│   4. Calculate scores                               │
└─────────────────────────────────────────────────────┘
Total embeddings: 101 (1 job + 100 candidate)
Optimization: 49.5% reduction in embedding computation
```

---

## 🧩 Module Dependencies

```
app/matching/ranking_orchestrator.py
│
├─→ app/matching/feature_extractor.py
│   │
│   ├─→ sentence_transformers (ML model)
│   ├─→ app/models/job.py
│   ├─→ app/models/student.py
│   ├─→ app/models/resume.py
│   └─→ json (for parsing resume embeddings)
│
├─→ app/matching/scoring_engine.py
│   │
│   ├─→ numpy
│   ├─→ sklearn.metrics.pairwise (cosine_similarity)
│   └─→ sentence_transformers (for skills matching)
│
├─→ app/models/application.py
├─→ app/database.py (AsyncSession)
└─→ sqlalchemy (async queries)
```

---

## 🔢 Scoring Algorithm Breakdown

```
┌────────────────────────────────────────────────────────────────┐
│                 40/40/20 Scoring Formula                       │
└────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   SEMANTIC   │    │    SKILLS    │    │  EXPERIENCE  │
│   (40%)      │    │    (40%)     │    │   (20%)      │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Cosine       │    │ Jaccard 40% +│    │ Linear ratio:│
│ similarity   │    │ Semantic 60% │    │ candidate/   │
│ of job &     │    │              │    │ required     │
│ candidate    │    │ Compare:     │    │              │
│ embeddings   │    │ - Required   │    │ 2.5 years /  │
│              │    │   skills     │    │ 2 years =    │
│ Result:      │    │ - Candidate  │    │ 1.25 → 100%  │
│ 0.823        │    │   skills     │    │              │
│              │    │              │    │ Result:      │
│              │    │ Result:      │    │ 100.0        │
│              │    │ 75.0         │    │              │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │    WEIGHTED COMBINATION      │
            │                              │
            │ (0.823 * 0.4)  = 0.3292      │
            │ (75.0/100 * 0.4) = 0.3000    │
            │ (100.0/100 * 0.2) = 0.2000   │
            │ ─────────────────────────    │
            │ Total: 0.8292                │
            │                              │
            │ Final: 0.8292 * 100 = 82.92  │
            └──────────────────────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │ OVERALL SCORE  │
                  │     82.92      │
                  └────────────────┘
```

---

## 📊 Performance Comparison

### Scenario: 100 Applications for 1 Job

#### OLD Implementation
```
┌─────────────────────────────────────────────┐
│ Application 1:                              │
│   - Fetch job ────────────────→ 20ms        │
│   - Generate job embedding ───→ 50ms ❌     │
│   - Fetch student ────────────→ 15ms        │
│   - Generate candidate embed ─→ 50ms        │
│   - Calculate similarity ─────→ 2ms         │
│   - Update DB ────────────────→ 10ms        │
│   Total: 147ms                              │
├─────────────────────────────────────────────┤
│ Application 2:                              │
│   - Fetch job ────────────────→ 20ms ❌     │
│   - Generate job embedding ───→ 50ms ❌     │
│   - Fetch student ────────────→ 15ms        │
│   - Generate candidate embed ─→ 50ms        │
│   - Calculate similarity ─────→ 2ms         │
│   - Update DB ────────────────→ 10ms        │
│   Total: 147ms                              │
├─────────────────────────────────────────────┤
│ ... (98 more applications)                  │
└─────────────────────────────────────────────┘
Total Time: 147ms × 100 = 14,700ms (14.7s)
Wasted: 99 × (20ms + 50ms) = 6,930ms (6.9s)
```

#### NEW Implementation
```
┌─────────────────────────────────────────────┐
│ BEFORE LOOP (ONCE):                         │
│   - Fetch job ────────────────→ 20ms ✓      │
│   - Generate job embedding ───→ 50ms ✓      │
│   Total: 70ms                               │
├─────────────────────────────────────────────┤
│ Application 1:                              │
│   - Fetch student ────────────→ 15ms        │
│   - Generate candidate embed ─→ 50ms        │
│   - Calculate similarity ─────→ 2ms         │
│   - Update DB ────────────────→ 10ms        │
│   Total: 77ms                               │
├─────────────────────────────────────────────┤
│ Application 2:                              │
│   - Fetch student ────────────→ 15ms        │
│   - Generate candidate embed ─→ 50ms        │
│   - Calculate similarity ─────→ 2ms         │
│   - Update DB ────────────────→ 10ms        │
│   Total: 77ms                               │
├─────────────────────────────────────────────┤
│ ... (98 more applications)                  │
└─────────────────────────────────────────────┘
Total Time: 70ms + (77ms × 100) = 7,770ms (7.77s)
Savings: 14,700ms - 7,770ms = 6,930ms (47% faster!)
```

---

## 🎯 Class Responsibilities

```
┌──────────────────────────────────────────────────────────┐
│  FeatureExtractor                                        │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Responsibilities:                                  │  │
│  │ • Extract structured data from models             │  │
│  │ • Parse skills (comma-separated → list)           │  │
│  │ • Estimate experience years                       │  │
│  │ • Generate embedding vectors                      │  │
│  │ • Load sentence-transformer model (lazy)          │  │
│  │                                                   │  │
│  │ Input: Job/Student/Resume models                  │  │
│  │ Output: JobFeatures/CandidateFeatures dataclasses │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  ScoringEngine                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Responsibilities:                                  │  │
│  │ • Calculate semantic similarity (cosine)          │  │
│  │ • Calculate skills match (Jaccard + semantic)     │  │
│  │ • Calculate experience match (linear)             │  │
│  │ • Combine scores using 40/40/20 formula           │  │
│  │                                                   │  │
│  │ Input: JobFeatures + CandidateFeatures            │  │
│  │ Output: ScoreBreakdown dataclass                  │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  RankingOrchestrator                                     │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Responsibilities:                                  │  │
│  │ • Orchestrate complete ranking workflow           │  │
│  │ • Fetch job and applications from database        │  │
│  │ • Coordinate FeatureExtractor and ScoringEngine   │  │
│  │ • Persist scores to database                      │  │
│  │ • Assign ranks based on scores                    │  │
│  │ • Generate AI summaries                           │  │
│  │ • Handle errors and transactions                  │  │
│  │                                                   │  │
│  │ Input: job_id or application_id + database session│  │
│  │ Output: Ranking results dictionary                │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## 📏 Data Structures

```
CandidateFeatures
┌─────────────────────────────────────┐
│ student_id: int                     │
│ application_id: int                 │
│ name: str                           │
│ skills: List[str]                   │ ← Parsed from comma-separated
│ experience_years: float             │ ← Estimated from graduation year
│ education: str                      │
│ cgpa: Optional[float]               │
│ university: Optional[str]           │
│ profile_embedding: List[float]      │ ← 384 dimensions
│ raw_profile_text: str               │
│ resume_text: Optional[str]          │
└─────────────────────────────────────┘

JobFeatures
┌─────────────────────────────────────┐
│ job_id: int                         │
│ title: str                          │
│ required_skills: List[str]          │ ← Parsed from comma-separated
│ required_experience_years: int      │
│ education_level: Optional[str]      │
│ job_embedding: List[float]          │ ← 384 dims (COMPUTED ONCE)
│ raw_job_text: str                   │
└─────────────────────────────────────┘

ScoreBreakdown
┌─────────────────────────────────────┐
│ overall_score: float (0-100)        │
│ semantic_score: float (0-100)       │
│ skills_score: float (0-100)         │
│ experience_score: float (0-100)     │
└─────────────────────────────────────┘
```

---

**Architecture diagrams complete! 📊**
