# 🎓 Campus Placement Portal

An AI-powered campus recruitment platform that automates the entire placement process — from resume submission to intelligent candidate ranking — for colleges, students, and recruiters.

---

## 📌 Table of Contents

- [About the Project](#about-the-project)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [API Documentation](#api-documentation)
- [Default Credentials](#default-credentials)
- [How It Works](#how-it-works)
- [Future Scope](#future-scope)

---

## 🧠 About the Project

Traditional campus placement is slow, manual, and often unfair. Recruiters post jobs, hundreds of students apply, and placement officers spend days shortlisting candidates by hand.

This portal automates that pipeline:
- Students upload resumes → AI parses and extracts skills
- Recruiters post jobs with eligibility criteria
- AI engine scores and ranks every applicant based on **skills match**, **experience**, and **semantic relevance**
- Placement officers approve drives and monitor placement stats in real-time

Built for a **single-college deployment** with role-based access for Students, Recruiters, Placement Officers, and Admins.

---

## ✨ Features

### 👨‍🎓 Student
- Register, login, manage profile
- Browse and apply to approved job drives
- View application status + AI match scores
- Upload resume (PDF/DOCX) for AI parsing

### 🏢 Recruiter
- Post job openings with eligibility criteria (CGPA, branch, backlogs)
- View AI-ranked candidate list with strengths/weaknesses
- Update application status (shortlist / reject / accept)

### 🧑‍💼 Placement Officer
- Approve or reject job drives before students can apply
- Monitor placement rates and student stats
- View all applications across the college

### 🔧 Admin
- System-wide overview (students, recruiters, jobs, placements)
- Manage users and college settings

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, Vite, React Query, React Router |
| **Backend** | FastAPI (Python), SQLAlchemy, asyncpg |
| **Database** | PostgreSQL |
| **AI** | Google Gemini API (matching + summary generation) |
| **Auth** | JWT (access + refresh tokens), RBAC |
| **Resume Parsing** | PyPDF2 / python-docx |

---

## 📁 Project Structure

```
Project 1/
├── Backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/             # Route handlers (auth, jobs, students...)
│   │   ├── models/             # SQLAlchemy DB models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── matching/           # AI ranking engine
│   │   │   ├── scoring_engine.py
│   │   │   └── ranking_orchestrator.py  # Gemini AI integration
│   │   └── core/               # Config, security, RBAC
│   ├── scripts/
│   │   └── seed_data.py        # Seed initial college + admin accounts
│   ├── requirements.txt
│   └── .env                    # Environment variables
│
├── Frontend/                   # React frontend
│   ├── src/
│   │   ├── pages/              # All page components
│   │   ├── context/            # AuthContext (login/register state)
│   │   ├── services/           # API service layer (axios)
│   │   └── routes.tsx          # Protected route definitions
│   ├── .env                    # Frontend env (API URL)
│   └── vite.config.ts          # Vite config + proxy
│
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (running locally)
- Google Gemini API Key ([get one here](https://makersuite.google.com/app/apikey))

---

### Backend Setup

```bash
cd Backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Edit .env with your DB credentials and Gemini API key

# Run database migrations (create tables)
# Tables are auto-created on first run

# Seed initial data (college + admin accounts)
python scripts/seed_data.py

# Start the backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be live at: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

---

### Frontend Setup

```bash
cd Frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend will be live at: `http://localhost:3000`

---

### Backend `.env` Configuration

```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/campus_placement_db
SECRET_KEY=your-secret-key-here
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL_NAME=gemini-1.5-flash
COLLEGE_ID=1
COLLEGE_NAME=College X
SINGLE_COLLEGE_MODE=True
```

---

## 📖 API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register/student` | Register a student |
| `POST` | `/api/v1/auth/register/recruiter` | Register a recruiter |
| `POST` | `/api/v1/auth/login/json` | Login (returns JWT token) |
| `GET` | `/api/v1/jobs` | List all approved jobs |
| `POST` | `/api/v1/applications` | Apply to a job |
| `GET` | `/api/v1/students/me/applications` | My applications |
| `POST` | `/api/v1/applications/job/{id}/rank` | Trigger AI ranking |

---

## 🔑 Default Credentials

After running `seed_data.py`:

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@collegex.edu` | `admin123` |
| Placement Officer | `placement@collegex.edu` | `placement123` |

> ⚠️ Change these passwords before deploying to production!

---

## ⚙️ How the AI Matching Works

```
Student applies to a Job
         ↓
Eligibility Check (CGPA, backlogs, placement status)
         ↓
      Eligible?
     ↙        ↘
  YES           NO → Status: REJECTED (eligibility_failed)
   ↓
AI Scoring:
  - Skills Match Score    (40%) → Jaccard similarity on skills  
  - Experience Score      (30%) → Experience years comparison
  - Semantic Score        (30%) → Gemini embedding similarity
         ↓
Gemini generates:
  - AI Summary
  - Candidate Strengths
  - Candidate Weaknesses
         ↓
Applications ranked by total score
Recruiter sees sorted leaderboard
```

---

## 🔭 Future Scope

- 📧 **Email/SMS Notifications** — Alert students when shortlisted
- 🏫 **Multi-college SaaS** — Each college gets its own subdomain
- 📄 **Resume Builder** — AI suggests improvements based on target jobs
- 🎥 **Video Interview Module** — Integrated async video screening
- 📊 **Advanced Analytics** — Year-on-year placement trends, company stats
- 📱 **Mobile App** — React Native version for students
- 🔗 **LinkedIn Integration** — Auto-fill profile + apply with LinkedIn resume
- ⚖️ **Bias Detection** — Flag algorithmic bias in rankings
- 📝 **Offer Letter Generator** — Auto-generate PDF offer letters on acceptance

---

## 👨‍💻 Author

**Gourav Kumar Singh**
- GitHub: [@gourav3649](https://github.com/gourav3649)

---

## 📄 License

This project is for educational purposes. MIT License.
