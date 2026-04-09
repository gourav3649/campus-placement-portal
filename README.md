# Placement Management System - Project 1

## Project Overview

A comprehensive placement management system designed to streamline the job placement process by leveraging AI-powered matching between student resumes and job descriptions. The system connects students, recruiters, and drives through an intelligent ranking engine.

**Current Focus:** Step 2 - AI-Powered Resume-to-Job Matching & Ranking

---

## What This Project Does

This system automates the recruitment process by:
1. **Student Job Discovery** - Students browse and apply to open jobs with their resumes
2. **Automated Eligibility Checking** - Only eligible students proceed to ranking
3. **AI Resume Matching** - Uses embedding-based cosine similarity to rank students by resume-job fit
4. **Recruiter Dashboard** - Shows top matching candidates ranked by AI score
5. **Single Source of Truth** - All rankings stored in database (no on-demand recomputation)

---

## ✅ What's Implemented

### **Phase 1: Application Submission & Eligibility**
- ✅ Students can submit job applications with resume selection
- ✅ Automatic eligibility checking before application creation
- ✅ Only eligible applications trigger AI matching

### **Phase 2: AI-Powered Ranking (COMPLETE)**

#### **Core Algorithm**
- **Pure Embedding-Based Cosine Similarity**
- Compares resume embeddings with job description embeddings
- No feature extraction, keyword matching, or heuristic scoring
- Single scoring layer: `ai_rank_score` field in Application model
- Score range: -1 to 1 (raw cosine similarity, not clamped)

#### **Database Optimization**
- **Batch Join Queries** - Eliminates N+1 query problem
- Single query fetches all applications with resumes: `select(Application, Resume).join(Resume, ...)`
- Batch commit of scores to database
- Efficient filtering by `is_eligible == True` and `ai_rank_score.isnot(None)`

#### **Ranking Service** (`app/services/ranking_service.py`)
Key functions:
- `rank_applications_for_job(job_id, db)` - Compute cosine similarity for all eligible applications
- `update_application_scores(job_id, db)` - Store scores in `ai_rank_score` field
- `get_ranked_applications(job_id, db)` - Return sorted list with ranks

#### **API Endpoints - Single Source of Truth**
All endpoints read from **stored** `ai_rank_score` (no recomputation):

| Endpoint | Method | Purpose | Who Can Access |
|----------|--------|---------|-----------------|
| `/applications` | POST | Submit application | Students (triggers background ranking) |
| `/applications/{application_id}` | GET | View details | Student (own) / Recruiter (their jobs) |
| `/applications/job/{job_id}/list` | GET | List all applications | Recruiter (their jobs) |
| `/applications/{application_id}/status` | PUT | Update status | Recruiter (their jobs) |
| `/applications/job/{job_id}/rank` | POST | Trigger ranking | Recruiter (their jobs) - background task |
| `/applications/job/{job_id}/ranked` | GET | View top N ranked | Recruiter (their jobs) dashboard |
| `/applications/{application_id}/ranking` | GET | Student views their rank | Students (their apps) |
| `/applications/job/{job_id}/top_candidates` | GET | Top candidates dashboard | Recruiter (their jobs) |

**Consistency Standards:**
- ✅ All endpoints use `is_eligible == True` filter
- ✅ All ranking queries: `order_by(Application.ai_rank_score.desc().nullslast())`
- ✅ Student and recruiter see identical rank positions
- ✅ No on-demand recomputation (single source of truth)
- ✅ Null-safe ordering ensures unranked apps appear at end

#### **Data Models**

**Application Model:**
```python
class Application:
    id: int                          # Primary key
    student_id: int                 # Foreign key to Student
    job_id: int                     # Foreign key to Job
    resume_id: int                  # Foreign key to Resume
    ai_rank_score: float | None     # Cosine similarity (-1 to 1)
    is_eligible: bool               # Eligibility filter
    status: ApplicationStatus       # PENDING, REVIEWED, SELECTED, REJECTED
    applied_at: datetime
```

**Response Schemas:**
- `ApplicationRanking` - Recruiter view of ranked applications
- `CandidatePreview` - Top candidates dashboard with email
- `StudentRankingView` - Student's ranking on specific job
- `ApplicationSchema` - Standard application details

#### **Query Patterns**
All ranking queries follow this pattern:
```python
select(Application)
  .filter(Application.job_id == job_id)
  .filter(Application.is_eligible == True)
  .filter(Application.ai_rank_score.isnot(None))
  .order_by(Application.ai_rank_score.desc().nullslast())
  .limit(top_n)
```

---

## 🟡 What's Left (TODO)

### **Phase 3: Frontend Integration**
- [ ] React/Vue components for student dashboard
- [ ] Recruiter dashboard UI to view top candidates
- [ ] Job posting interface
- [ ] Resume management interface
- [ ] Real-time ranking visualization

### **Phase 4: Advanced Ranking Features**
- [ ] Re-ranking on demand with force flag support
- [ ] Batch application operations
- [ ] Pagination for large result sets
- [ ] Advanced filtering (by status, date, score range)

### **Phase 5: Notifications & Tracking**
- [ ] Email notifications to students (rank updates)
- [ ] Email notifications to recruiters (new applications)
- [ ] Activity log/audit trail
- [ ] Application timeline history

### **Phase 6: Analytics & Reporting**
- [ ] Recruitment funnel metrics
- [ ] Ranking distribution analysis
- [ ] Time-to-hire metrics
- [ ] Candidate quality scoring

### **Phase 7: Performance & Scalability**
- [ ] Caching layer (Redis) for frequent rankings
- [ ] Async background jobs (Celery) for bulk operations
- [ ] Database indexing optimization
- [ ] Load testing & performance benchmarking

### **Phase 8: Testing & Documentation**
- [ ] Unit tests for ranking_service.py
- [ ] Integration tests for API endpoints
- [ ] End-to-end tests for ranking workflow
- [ ] API documentation (Swagger/OpenAPI enhancement)
- [ ] Database schema documentation

---

## 🛠 Tech Stack

### Backend
- **Framework:** FastAPI
- **ORM:** SQLAlchemy (async)
- **Database:** PostgreSQL
- **Authentication:** JWT with role-based access control (STUDENT, RECRUITER, ADMIN)
- **Embeddings:** Sentence transformers / OpenAI embeddings
- **Async:** asyncio with AsyncSession

### Frontend (Not Started)
- React or Vue.js
- TypeScript
- State management (Redux/Zustand)
- UI library (Tailwind CSS)

---

## 🏃‍♂️ Running Locally

### Prerequisites
```
Python 3.10+
PostgreSQL 12+
pip (Python package manager)
```

### Backend Setup
```bash
cd Backend
pip install -r requirements.txt

# Verify setup
python -c "from app.api.v1 import applications; print('✓ Setup complete')"

# Create .env file with:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost/db_name
# SECRET_KEY=your-secret-key
# EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Run Development Server
```bash
cd Backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
Once running, visit: `http://localhost:8000/docs` (Swagger UI)

---

## Project Structure

```
Project 1/
├── Backend/
│   ├── app/
│   │   ├── api/v1/applications.py       # ✅ Application endpoints (8 endpoints)
│   │   ├── services/ranking_service.py  # ✅ Core ranking engine
│   │   ├── models/application.py        # ✅ Application ORM model
│   │   ├── schemas/application.py       # ✅ Request/response schemas
│   │   └── ...
│   ├── requirements.txt
│   └── .env
├── Frontend/
│   └── (not started)
└── README.md (this file)
```

---

## Key Implementation Details

### Single Source of Truth
- Only `ranking_service.py` computes cosine similarity scores
- All API endpoints read pre-computed scores from `ai_rank_score` field
- No endpoint recomputes scores (consistency guaranteed)

### Null-Safe Ordering
- All ranking queries use `.nullslast()` to push unranked apps to end
- Ensures consistent rank positions across all endpoints

### Batch Efficiency
- Uses `select(Application, Resume).join(Resume, ...)` for single query
- Eliminates N+1 database query problem
- Batch commits scores to database

### Eligibility Filtering
- Only `is_eligible == True` applications appear in rankings
- Applied consistently across all endpoints

---

## Status Summary

| Component | Status | Completion |
|-----------|--------|-----------|
| AI Ranking Algorithm | ✅ Complete | 100% |
| API Endpoints (8 endpoints) | ✅ Complete | 100% |
| Database Optimization | ✅ Complete | 100% |
| Consistency & Ordering | ✅ Complete | 100% |
| Frontend | 🟡 Not Started | 0% |
| Testing Suite | 🟡 Not Started | 0% |
| Deployment | 🟡 Not Started | 0% |
| **Overall** | **🟡 In Progress** | **~25%** |

---

## Next Steps

1. **Frontend Development** - Build React components for student/recruiter dashboards
2. **Testing** - Write unit and integration tests for ranking
3. **Deployment** - Setup Docker and CI/CD pipeline
4. **Scaling** - Add caching layer and async jobs
5. **Analytics** - Implement reporting endpoints

---

**Last Updated:** April 2026  
**Current Phase:** Step 2 - AI Ranking (Complete)  
**Next Phase:** Phase 3 - Frontend Integration
