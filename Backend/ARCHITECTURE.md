# Campus Placement Portal - Architecture Documentation

## 📐 System Architecture

### High-Level Architecture

```
┌─────────────────┐
│   React Frontend │
│   (Port 3000)   │
└────────┬────────┘
         │ HTTP/REST
         │
┌────────▼────────────────────────────────────┐
│         FastAPI Backend (Port 8000)         │
│  ┌──────────────────────────────────────┐   │
│  │         API Layer (v1)               │   │
│  │  - Auth  - Students  - Recruiters   │   │
│  │  - Jobs  - Applications              │   │
│  └──────────────┬───────────────────────┘   │
│                 │                            │
│  ┌──────────────▼───────────────────────┐   │
│  │      Business Logic Layer            │   │
│  │  - RBAC  - Security  - Validation   │   │
│  └──────────────┬───────────────────────┘   │
│                 │                            │
│  ┌──────────────▼───────────────────────┐   │
│  │       AI Services Layer              │   │
│  │  - Resume Parser                     │   │
│  │  - Semantic Ranking                  │   │
│  │  - Background Tasks                  │   │
│  └──────────────┬───────────────────────┘   │
│                 │                            │
│  ┌──────────────▼───────────────────────┐   │
│  │      Data Access Layer               │   │
│  │  - SQLAlchemy ORM (Async)           │   │
│  │  - Database Models                   │   │
│  └──────────────┬───────────────────────┘   │
└─────────────────┼──────────────────────────┘
                  │
        ┌─────────▼─────────┐
        │   PostgreSQL DB   │
        │   (Port 5432)     │
        └───────────────────┘

        ┌───────────────────┐
        │   Redis Cache     │
        │   (Port 6379)     │
        └───────────────────┘
```

## 🏗️ Backend Architecture

### Layer Structure

#### 1. **API Layer** (`app/api/`)
- **Purpose**: Handle HTTP requests and responses
- **Components**:
  - Route handlers for each resource
  - Request validation using Pydantic
  - Response formatting
  - Error handling

#### 2. **Core Layer** (`app/core/`)
- **Purpose**: Core business logic and configurations
- **Components**:
  - `config.py`: Application settings
  - `security.py`: JWT authentication, password hashing
  - `rbac.py`: Role-Based Access Control

#### 3. **Models Layer** (`app/models/`)
- **Purpose**: Database schema definitions
- **Components**:
  - SQLAlchemy models for all entities
  - Relationships and constraints
  - Database indexes

#### 4. **Schemas Layer** (`app/schemas/`)
- **Purpose**: Request/Response validation
- **Components**:
  - Pydantic models for API contracts
  - Input validation
  - Output serialization

#### 5. **Services Layer** (`app/services/`)
- **Purpose**: Business logic and AI features
- **Components**:
  - `resume_parser.py`: PDF/DOCX parsing
  - `semantic_ranking.py`: AI-powered candidate matching
  - Background task processors

## 🔐 Authentication & Authorization

### Authentication Flow

```
1. User Registration
   ├─> Create User record
   ├─> Create role-specific profile (Student/Recruiter)
   └─> Hash password with bcrypt

2. Login
   ├─> Verify credentials
   ├─> Generate JWT access token (30 min)
   ├─> Generate JWT refresh token (7 days)
   └─> Return tokens

3. Protected Routes
   ├─> Extract JWT from Authorization header
   ├─> Validate token signature
   ├─> Extract user ID and role
   ├─> Load user from database
   └─> Check permissions
```

### Role-Based Access Control (RBAC)

#### Roles:
- **Student**: Can view jobs, submit applications, manage profile
- **Recruiter**: Can post jobs, view applicants, access AI rankings
- **Admin**: Full system access (future implementation)

#### Permission Mapping:
```python
STUDENT:
  - VIEW_JOBS
  - APPLY_TO_JOBS
  - MANAGE_OWN_PROFILE
  - UPLOAD_RESUME
  - VIEW_OWN_APPLICATIONS

RECRUITER:
  - VIEW_JOBS
  - POST_JOBS
  - MANAGE_OWN_JOBS
  - VIEW_APPLICANTS
  - RANK_CANDIDATES
  - UPDATE_APPLICATION_STATUS
```

## 🤖 AI Components

### 1. Resume Parser

**Technology**: pdfplumber, python-docx, regex, NLP

**Process**:
```
Resume Upload
   ├─> File validation (PDF/DOCX, size < 10MB)
   ├─> Extract raw text
   ├─> Parse structured data
   │   ├─> Contact information
   │   ├─> Skills (keyword matching)
   │   ├─> Education history
   │   ├─> Work experience
   │   └─> Certifications
   └─> Store in database
```

### 2. Semantic Ranking

**Technology**: sentence-transformers, scikit-learn, numpy

**Process**:
```
Application Submission
   ├─> Trigger background task
   ├─> Generate embeddings
   │   ├─> Job description embedding
   │   └─> Candidate profile embedding
   ├─> Calculate similarity scores
   │   ├─> Overall semantic match (40%)
   │   ├─> Skills match (40%)
   │   └─> Experience match (20%)
   ├─> Generate AI summary
   │   ├─> Strengths
   │   └─> Weaknesses
   └─> Assign rank among all applicants
```

**Matching Algorithm**:
```python
Overall Score = (
    semantic_similarity * 0.4 +
    skills_match * 0.4 +
    experience_match * 0.2
) * 100
```

## 📊 Database Schema

### Entity Relationships

```
User (1) ──┬── (1) Student
           └── (1) Recruiter

Student (1) ── (*) Resume
Student (1) ── (*) Application

Recruiter (1) ── (*) Job

Job (1) ── (*) Application

Application (*) ── (1) Resume
```

### Key Tables

1. **users**: Authentication and role assignment
2. **students**: Student profiles and academic info
3. **recruiters**: Company and recruiter information
4. **jobs**: Job postings with requirements
5. **applications**: Job applications with AI scores
6. **resumes**: Parsed resume data and embeddings

## ⚡ Performance Optimizations

### 1. Asynchronous Operations
- All database queries use `async/await`
- Non-blocking I/O for API requests
- Concurrent request handling

### 2. Background Tasks
- Resume parsing runs asynchronously
- AI ranking processes in background
- No user blocking for heavy operations

### 3. Database Optimizations
- Indexes on frequently queried fields
- Connection pooling (pool_size=10)
- Lazy loading of relationships

### 4. Caching Strategy (Future)
- Redis for session storage
- Cache frequently accessed jobs
- Cache AI embeddings

## 🔄 API Versioning

Current Version: **v1**

**URL Structure**: `/api/v1/{resource}`

**Benefits**:
- Backward compatibility
- Gradual migration
- Multiple versions can coexist

## 📈 Scalability Considerations

### Horizontal Scaling
- Stateless API design
- JWT tokens (no server-side sessions)
- Background task queue (Celery + Redis)

### Vertical Scaling
- Async operations reduce memory usage
- Connection pooling optimizes DB connections
- Efficient embedding storage

### Future Enhancements
- Load balancing with Nginx
- Database read replicas
- Distributed caching with Redis Cluster
- Microservices architecture for AI components

## 🛡️ Security Measures

1. **Password Security**
   - Bcrypt hashing with salt
   - Minimum 8 characters

2. **JWT Security**
   - Short-lived access tokens (30 min)
   - Refresh token rotation
   - Secret key from environment

3. **Input Validation**
   - Pydantic schema validation
   - SQL injection prevention (ORM)
   - XSS protection

4. **CORS Configuration**
   - Whitelist allowed origins
   - Credential support

## 🧪 Testing Strategy

### Test Levels
1. **Unit Tests**: Individual functions
2. **Integration Tests**: API endpoints
3. **E2E Tests**: Full user workflows

### Test Coverage
- Authentication flows
- RBAC enforcement
- AI ranking accuracy
- Database operations

## 📦 Deployment

### Development
```bash
uvicorn app.main:app --reload
```

### Production
```bash
# With Docker
docker-compose up -d

# Or with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Environment Variables
- Managed via `.env` file
- Never commit secrets
- Use secret management in production

## 🔧 Maintenance

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Monitoring
- Application logs
- Database query performance
- API response times
- Background task status

## 🎯 Future Roadmap

1. **Enhanced AI Features**
   - OpenAI integration for better summaries
   - Custom ML models for ranking
   - Interview scheduling recommendations

2. **Additional Features**
   - Email notifications
   - Real-time chat
   - Video interview integration
   - Analytics dashboard

3. **Performance**
   - GraphQL API
   - WebSocket support
   - Advanced caching

4. **Security**
   - OAuth2 integration
   - Two-factor authentication
   - Rate limiting
