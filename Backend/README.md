# AI-Driven Campus Placement Portal - Backend

A high-performance, scalable backend for campus placement management built with FastAPI, PostgreSQL, and AI-powered features.

## 🚀 Features

- **Asynchronous Architecture**: All database and API operations use async/await patterns
- **AI-Powered Resume Parsing**: Automatic extraction of skills, experience, and qualifications
- **Semantic Job Matching**: AI-driven ranking of candidates based on job requirements
- **Role-Based Access Control (RBAC)**: Separate permissions for Students and Recruiters
- **Background Processing**: Heavy AI tasks handled asynchronously
- **RESTful API**: Clean, versioned API endpoints
- **Type Safety**: Full Pydantic validation

## 📋 Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy (async)
- **Authentication**: JWT with role-based permissions
- **AI/ML**: OpenAI, LangChain, spaCy, Sentence Transformers
- **Background Tasks**: Celery + Redis
- **Testing**: Pytest with async support

## 🏗️ Architecture

```
app/
├── core/           # Core configurations, security, RBAC
├── models/         # SQLAlchemy database models
├── schemas/        # Pydantic schemas for validation
├── api/            # API routes organized by version
├── services/       # Business logic and AI services
└── utils/          # Helper functions and utilities
```

## 🔧 Setup Instructions

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual configuration
```

### 3. Run Database Migrations

```bash
alembic upgrade head
```

### 4. Start the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API Documentation

Once running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔐 Role-Based Access

### Student Role
- Create/update profile
- Upload resume
- Browse jobs
- Apply to jobs
- View application status

### Recruiter Role
- Post job opportunities
- View applicants
- Access AI-ranked candidates
- Manage job postings

## 🧪 Running Tests

```bash
pytest tests/ -v
```

## 📦 Key Endpoints

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/jobs` - List all jobs
- `POST /api/v1/applications` - Submit job application
- `GET /api/v1/applications/{id}/ranking` - Get AI-ranked candidates

## 🛠️ Development

This project follows clean code principles:
- Separation of concerns
- Dependency injection
- Type hints throughout
- Comprehensive error handling
- Async-first approach

## 📝 License

MIT License
