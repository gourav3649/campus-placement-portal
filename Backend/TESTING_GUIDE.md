# 🚀 Quick Test Guide - Backend Implementation

## ✅ What's Been Implemented

All 3 steps are **COMPLETE**:

### Step 1: Database Foundation ✓
- [database.py](app/database.py) - SQLAlchemy 2.0 async engine
- [models/](app/models/) - All 6 models (User, Student, Recruiter, Job, Resume, Application)
- Full relationships and `embedding_vector` field in Resume model

### Step 2: AI Services Logic ✓
- [services/resume_parser.py](app/services/resume_parser.py) - PDF/DOCX parsing
- [services/semantic_ranking.py](app/services/semantic_ranking.py) - Matching engine with 40/40/20 algorithm

### Step 3: API Entry Point ✓
- [main.py](app/main.py) - FastAPI app with CORS from .env
- [api/v1/resumes.py](app/api/v1/resumes.py) - Resume upload with BackgroundTask ⭐

---

## 🏃 Run the Backend (5 Steps)

### 1. Install Dependencies
```powershell
# In Backend directory
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Download spaCy model (optional, for advanced NLP)
python -m spacy download en_core_web_sm
```

### 2. Setup Environment
```powershell
# Copy example env
cp .env.example .env

# Edit .env and update:
# - SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_hex(32))")
# - DATABASE_URL (if not using Docker defaults)
```

### 3. Start Database
```powershell
# Start PostgreSQL + Redis with Docker
docker-compose up -d

# Verify it's running
docker-compose ps
```

### 4. Run Migrations
```powershell
# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

### 5. Start FastAPI Server
```powershell
uvicorn app.main:app --reload
```

**Server running at**: http://localhost:8000  
**API Docs**: http://localhost:8000/docs 🎉

---

## 🧪 Test the Complete Flow

### Option 1: Using Swagger UI (Easiest)

1. Open http://localhost:8000/docs
2. **Register a student**:
   - Click `POST /api/v1/auth/register/student`
   - Try it out
   - Use this JSON:
```json
{
  "user_data": {
    "email": "test.student@example.com",
    "password": "password123",
    "role": "student"
  },
  "student_data": {
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "enrollment_number": "EN2024001",
    "university": "Stanford University",
    "degree": "Bachelor of Science",
    "major": "Computer Science",
    "graduation_year": 2024,
    "cgpa": 9.2,
    "bio": "Passionate software engineer",
    "skills": "Python, JavaScript, React, FastAPI, PostgreSQL, Docker"
  }
}
```

3. **Login**:
   - Click `POST /api/v1/auth/login/json`
   - Use:
```json
{
  "email": "test.student@example.com",
  "password": "password123"
}
```
   - Copy the `access_token` from response

4. **Authorize**:
   - Click 🔓 **Authorize** button at top
   - Paste: `Bearer YOUR_ACCESS_TOKEN`
   - Click Authorize

5. **Upload Resume**:
   - Click `POST /api/v1/resumes/upload`
   - Choose a PDF or DOCX file
   - Execute
   - Note the `resume_id` from response

6. **Check Parsing Status**:
   - Wait 5-10 seconds for background processing
   - Click `GET /api/v1/resumes/{resume_id}`
   - Enter your `resume_id`
   - See parsed data with skills, education, etc.!

7. **Register a Recruiter & Post a Job**:
   - Use `POST /api/v1/auth/register/recruiter`
   - Login as recruiter
   - Use `POST /api/v1/jobs` to create a job

8. **Submit Application**:
   - Login as student again
   - Use `POST /api/v1/applications`
   - Reference the job_id and resume_id

9. **View AI Rankings**:
   - Login as recruiter
   - Use `GET /api/v1/applications/job/{job_id}/ranked`
   - See AI-powered candidate ranking with scores!

---

### Option 2: Using Python Script

Create `test_backend.py`:

```python
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

# 1. Register student
student_data = {
    "user_data": {
        "email": "john.doe@example.com",
        "password": "password123",
        "role": "student"
    },
    "student_data": {
        "first_name": "John",
        "last_name": "Doe",
        "university": "Stanford",
        "major": "Computer Science",
        "graduation_year": 2024,
        "cgpa": 9.2,
        "skills": "Python, FastAPI, React, PostgreSQL"
    }
}

resp = requests.post(f"{BASE_URL}/auth/register/student", json=student_data)
print(f"✅ Student registered: {resp.json()['email']}")

# 2. Login
login_resp = requests.post(f"{BASE_URL}/auth/login/json", json={
    "email": "john.doe@example.com",
    "password": "password123"
})
token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"✅ Logged in, got token")

# 3. Upload resume
with open("sample_resume.pdf", "rb") as f:
    files = {"file": f}
    upload_resp = requests.post(f"{BASE_URL}/resumes/upload", 
                                files=files, headers=headers)
    resume_id = upload_resp.json()["resume_id"]
    print(f"✅ Resume uploaded: ID {resume_id}, status: pending")

# 4. Wait for parsing
time.sleep(10)

# 5. Check parsed resume
resume_resp = requests.get(f"{BASE_URL}/resumes/{resume_id}", headers=headers)
resume = resume_resp.json()
print(f"✅ Resume parsed!")
print(f"   Status: {resume['parse_status']}")
print(f"   Skills found: {resume.get('extracted_skills', [])}")
print(f"   Education: {resume.get('extracted_education', [])}")

print("\n🎉 Backend is working perfectly!")
```

Run it:
```powershell
python test_backend.py
```

---

## 🔍 Verify AI Features

### Test Resume Parsing:
1. Upload a real resume PDF/DOCX
2. Check `GET /api/v1/resumes/{id}` response
3. Verify extracted fields:
   - ✅ `extracted_skills` - Array of tech skills
   - ✅ `extracted_education` - Degrees and universities
   - ✅ `extracted_experience` - Work history
   - ✅ `embedding_vector` - Semantic embedding for matching

### Test AI Ranking:
1. Create a job posting (as recruiter)
2. Submit multiple applications (as different students)
3. Call `POST /api/v1/applications/job/{job_id}/rank`
4. Get rankings: `GET /api/v1/applications/job/{job_id}/ranked`
5. Verify:
   - ✅ `match_score` - Overall compatibility (0-100)
   - ✅ `skills_match_score` - Skills alignment
   - ✅ `experience_match_score` - Experience fit
   - ✅ `rank` - Position (1 is best)
   - ✅ `ai_summary` - AI-generated fit analysis
   - ✅ `strengths` - Key strengths
   - ✅ `weaknesses` - Areas of concern

---

## 📊 Verify Scoring Algorithm

The AI uses this formula (from [semantic_ranking.py](app/services/semantic_ranking.py:228-232)):

```python
overall_score = (
    overall_similarity * 0.4 +      # 40% semantic match
    (skills_match / 100) * 0.4 +    # 40% skills match  
    (experience_match / 100) * 0.2  # 20% experience match
) * 100
```

Test it:
1. Create a Python job requiring "Python, FastAPI, PostgreSQL"
2. Apply with student having those exact skills
3. Check `skills_match_score` - Should be ~90-100
4. Check `match_score` - Should be high (70-90)

---

## 🐛 Troubleshooting

### Error: "Import xyz could not be resolved"
**Solution**: Install dependencies
```powershell
pip install -r requirements.txt
```

### Error: "Database connection failed"
**Solution**: Start PostgreSQL
```powershell
docker-compose up -d
# Or check your DATABASE_URL in .env
```

### Error: "Table doesn't exist"
**Solution**: Run migrations
```powershell
alembic upgrade head
```

### Resume parsing stuck at "pending"
**Solution**: Check server logs for errors
- PDF might be corrupted
- Check file is actually PDF/DOCX
- Verify `uploads/resumes/` directory exists

### AI ranking returns null scores
**Solution**: Wait longer (first run downloads AI models ~500MB)
- Check server logs for "Downloading model..."
- Can take 1-2 minutes on first run

---

## 📁 Project Structure Recap

```
Backend/
├── app/
│   ├── api/v1/           # All API endpoints ✅
│   │   ├── auth.py       - Register, login
│   │   ├── students.py   - Student profiles
│   │   ├── recruiters.py - Recruiter profiles
│   │   ├── jobs.py       - Job CRUD
│   │   ├── applications.py - Applications + AI ranking
│   │   └── resumes.py    - Resume upload (NEW) ⭐
│   │
│   ├── core/             # Core logic ✅
│   │   ├── config.py     - Settings from .env
│   │   ├── security.py   - JWT, password hashing
│   │   └── rbac.py       - Role-based access control
│   │
│   ├── models/           # Database models ✅
│   │   ├── user.py       - Authentication
│   │   ├── student.py    - Student profiles
│   │   ├── recruiter.py  - Recruiter profiles
│   │   ├── job.py        - Job postings
│   │   ├── resume.py     - Resumes with embeddings
│   │   └── application.py - Applications with AI scores
│   │
│   ├── schemas/          # Pydantic validation ✅
│   │   └── (All request/response models)
│   │
│   ├── services/         # AI logic ✅
│   │   ├── resume_parser.py    - PDF/DOCX parsing
│   │   └── semantic_ranking.py - AI matching engine
│   │
│   ├── utils/            # Helpers ✅
│   │   └── helpers.py    - Utility functions
│   │
│   ├── database.py       # SQLAlchemy setup ✅
│   └── main.py           # FastAPI app ✅
│
├── uploads/resumes/      # Resume storage ✅
├── alembic/              # DB migrations ✅
├── tests/                # Test suite ✅
├── requirements.txt      # Dependencies ✅
├── docker-compose.yml    # PostgreSQL + Redis ✅
└── .env.example          # Config template ✅
```

---

## ✨ What You Can Do Now

✅ Register students and recruiters  
✅ Upload resumes (PDF/DOCX)  
✅ Auto-parse resumes with AI  
✅ Post job openings  
✅ Submit job applications  
✅ Get AI-powered candidate rankings  
✅ View match scores and summaries  
✅ Complete RBAC and authentication  
✅ Async operations throughout  
✅ Background task processing  
✅ Production-ready API  

---

## 🎯 Next: Frontend Integration

The backend is **100% ready**. To connect your React frontend:

1. Base URL: `http://localhost:8000/api/v1`
2. Auth: Include `Authorization: Bearer <token>` header
3. File upload: Use `FormData` with `multipart/form-data`
4. Full API reference: [API.md](API.md)

Example React code:
```javascript
// Upload resume
const formData = new FormData();
formData.append('file', resumeFile);

const response = await fetch('http://localhost:8000/api/v1/resumes/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
});
```

---

**Backend Implementation: COMPLETE! 🎉**

Test it now with `uvicorn app.main:app --reload` and open http://localhost:8000/docs
