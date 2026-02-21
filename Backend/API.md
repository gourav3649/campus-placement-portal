# API Reference - Campus Placement Portal

## Base URL
```
Development: http://localhost:8000/api/v1
Production: https://your-domain.com/api/v1
```

## Authentication

All protected endpoints require JWT Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## 🔐 Authentication Endpoints

### Register Student
**POST** `/auth/register/student`

Register a new student user and create student profile.

**Request Body:**
```json
{
  "user_data": {
    "email": "student@example.com",
    "password": "password123",
    "role": "student"
  },
  "student_data": {
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "enrollment_number": "EN123456",
    "university": "MIT",
    "degree": "Bachelor of Science",
    "major": "Computer Science",
    "graduation_year": 2024,
    "cgpa": 9.2,
    "bio": "Passionate software engineer",
    "linkedin_url": "https://linkedin.com/in/johndoe",
    "github_url": "https://github.com/johndoe",
    "portfolio_url": "https://johndoe.dev",
    "skills": "Python, JavaScript, React, FastAPI"
  }
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "email": "student@example.com",
  "role": "student",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-02-18T10:00:00Z"
}
```

### Register Recruiter
**POST** `/auth/register/recruiter`

Register a new recruiter user and create recruiter profile.

**Request Body:**
```json
{
  "user_data": {
    "email": "recruiter@techcorp.com",
    "password": "password123",
    "role": "recruiter"
  },
  "recruiter_data": {
    "company_name": "Tech Corp",
    "company_website": "https://techcorp.com",
    "company_description": "Leading technology company",
    "first_name": "Jane",
    "last_name": "Smith",
    "position": "HR Manager",
    "phone": "+1987654321",
    "linkedin_url": "https://linkedin.com/in/janesmith"
  }
}
```

### Login (JSON)
**POST** `/auth/login/json`

Login and receive access/refresh tokens.

**Request Body:**
```json
{
  "email": "student@example.com",
  "password": "password123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Login (OAuth2)
**POST** `/auth/login`

OAuth2 password flow login (for compatibility).

**Form Data:**
- `username`: Email address
- `password`: User password

---

## 👨‍🎓 Student Endpoints

### Get My Profile
**GET** `/students/me`

Get current student's profile.

**Auth Required:** Student role

**Response:** `200 OK`
```json
{
  "id": 1,
  "user_id": 1,
  "email": "student@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "enrollment_number": "EN123456",
  "university": "MIT",
  "degree": "Bachelor of Science",
  "major": "Computer Science",
  "graduation_year": 2024,
  "cgpa": 9.2,
  "bio": "Passionate software engineer",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "github_url": "https://github.com/johndoe",
  "portfolio_url": "https://johndoe.dev",
  "skills": "Python, JavaScript, React, FastAPI",
  "created_at": "2024-02-18T10:00:00Z"
}
```

### Update My Profile
**PUT** `/students/me`

Update current student's profile.

**Auth Required:** Student role

**Request Body:** (all fields optional)
```json
{
  "first_name": "John",
  "bio": "Updated bio",
  "skills": "Python, JavaScript, React, FastAPI, PostgreSQL"
}
```

### Get My Applications
**GET** `/students/me/applications`

Get all applications submitted by current student.

**Auth Required:** Student role

**Response:** Array of applications

### Get Student Profile
**GET** `/students/{student_id}`

Get a specific student's profile (public info).

**Auth Required:** Any authenticated user

---

## 🏢 Recruiter Endpoints

### Get My Profile
**GET** `/recruiters/me`

Get current recruiter's profile.

**Auth Required:** Recruiter role

### Update My Profile
**PUT** `/recruiters/me`

Update current recruiter's profile.

**Auth Required:** Recruiter role

### Get My Jobs
**GET** `/recruiters/me/jobs`

Get all jobs posted by current recruiter.

**Auth Required:** Recruiter role

---

## 💼 Job Endpoints

### Create Job
**POST** `/jobs`

Create a new job posting.

**Auth Required:** Recruiter role

**Request Body:**
```json
{
  "title": "Senior Software Engineer",
  "description": "We are looking for an experienced software engineer...",
  "requirements": "5+ years of experience in Python, FastAPI...",
  "responsibilities": "Design and develop scalable APIs...",
  "job_type": "full_time",
  "location": "San Francisco, CA",
  "is_remote": true,
  "salary_min": 120000,
  "salary_max": 180000,
  "currency": "USD",
  "required_skills": "Python, FastAPI, PostgreSQL, Docker",
  "experience_years": 5,
  "education_level": "Bachelor's Degree",
  "positions_available": 2,
  "deadline": "2024-03-31T23:59:59Z"
}
```

**Response:** `201 Created` - Job object

### List Jobs
**GET** `/jobs`

List all open jobs with pagination and filters.

**Auth Required:** Any authenticated user

**Query Parameters:**
- `skip` (int): Offset for pagination (default: 0)
- `limit` (int): Number of items per page (default: 20, max: 100)
- `job_type` (string): Filter by job type
- `location` (string): Filter by location (partial match)
- `is_remote` (bool): Filter remote jobs

**Response:** `200 OK`
```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "jobs": [...]
}
```

### Get Job
**GET** `/jobs/{job_id}`

Get details of a specific job.

**Auth Required:** Any authenticated user

### Update Job
**PUT** `/jobs/{job_id}`

Update a job posting.

**Auth Required:** Recruiter role (must own the job)

### Delete Job
**DELETE** `/jobs/{job_id}`

Delete a job posting.

**Auth Required:** Recruiter role (must own the job)

**Response:** `204 No Content`

### Close Job
**POST** `/jobs/{job_id}/close`

Close a job posting (stop accepting applications).

**Auth Required:** Recruiter role (must own the job)

---

## 📝 Application Endpoints

### Submit Application
**POST** `/applications`

Submit a job application.

**Auth Required:** Student role

**Request Body:**
```json
{
  "job_id": 1,
  "resume_id": 1,
  "cover_letter": "I am very interested in this position..."
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "student_id": 1,
  "job_id": 1,
  "resume_id": 1,
  "status": "pending",
  "cover_letter": "I am very interested...",
  "match_score": null,
  "applied_at": "2024-02-18T10:00:00Z"
}
```

**Note:** AI matching runs in the background. Match scores will be available shortly.

### Get Application
**GET** `/applications/{application_id}`

Get details of a specific application.

**Auth Required:** 
- Students can view their own applications
- Recruiters can view applications for their jobs

### Update Application Status
**PUT** `/applications/{application_id}/status`

Update application status.

**Auth Required:** Recruiter role (must own the job)

**Query Parameters:**
- `new_status`: ApplicationStatus enum value

**Valid Statuses:**
- `pending`
- `reviewing`
- `shortlisted`
- `rejected`
- `accepted`
- `withdrawn`

### List Job Applications
**GET** `/applications/job/{job_id}/list`

List all applications for a specific job.

**Auth Required:** Recruiter role (must own the job)

**Query Parameters:**
- `status_filter`: Filter by application status

**Response:** Array of applications sorted by rank/match score

### Trigger AI Ranking
**POST** `/applications/job/{job_id}/rank`

Trigger AI-powered ranking of all applications for a job.

**Auth Required:** Recruiter role (must own the job)

**Query Parameters:**
- `rerank` (bool): Force re-ranking of already processed applications

**Response:** `202 Accepted`
```json
{
  "message": "AI ranking process started",
  "job_id": 1,
  "status": "processing"
}
```

**Note:** This is a background task. Check application scores after processing.

### Get Ranked Applications
**GET** `/applications/job/{job_id}/ranked`

Get AI-ranked applications for a job.

**Auth Required:** Recruiter role (must own the job)

**Query Parameters:**
- `top_n` (int): Number of top candidates to return (default: 10, max: 100)

**Response:** `200 OK`
```json
[
  {
    "application_id": 1,
    "student_id": 1,
    "student_name": "John Doe",
    "match_score": 87.5,
    "skills_match_score": 90.0,
    "experience_match_score": 85.0,
    "rank": 1,
    "ai_summary": "Excellent candidate for Senior Software Engineer...",
    "strengths": [
      "Strong alignment with required technical skills",
      "Excellent academic performance (CGPA: 9.20)"
    ],
    "weaknesses": [
      "May lack required experience level"
    ],
    "resume_url": null
  }
]
```

---

## 📄 Response Codes

### Success Codes
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `202 Accepted`: Request accepted for processing
- `204 No Content`: Request successful, no content to return

### Client Error Codes
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error

### Server Error Codes
- `500 Internal Server Error`: Server error

---

## 🔄 AI Features

### Resume Parsing
When a student uploads a resume, the system:
1. Validates file format (PDF/DOCX)
2. Extracts text content
3. Parses structured information:
   - Contact details
   - Skills
   - Education
   - Work experience
   - Certifications
4. Generates semantic embeddings

### Semantic Ranking
When an application is submitted:
1. Extract job requirements
2. Extract candidate profile
3. Generate embeddings for both
4. Calculate similarity scores:
   - Overall semantic match
   - Skills compatibility
   - Experience alignment
5. Generate AI summary with strengths/weaknesses
6. Rank among all applicants

### Scoring Algorithm
```
Overall Score = (
    semantic_similarity * 40% +
    skills_match * 40% +
    experience_match * 20%
) * 100
```

---

## 📊 Data Models

### Job Types
- `full_time`
- `part_time`
- `internship`
- `contract`

### Job Status
- `open`: Accepting applications
- `closed`: No longer accepting applications
- `draft`: Not yet published

### Application Status
- `pending`: Submitted, awaiting review
- `reviewing`: Under review
- `shortlisted`: Selected for next round
- `rejected`: Not selected
- `accepted`: Offer extended
- `withdrawn`: Withdrawn by student

---

## 🔒 Security

### Password Requirements
- Minimum 8 characters
- Hashed using bcrypt

### Token Expiration
- Access Token: 30 minutes
- Refresh Token: 7 days

### Rate Limiting
Not yet implemented. Recommended for production.

---

## 📝 Notes

1. All timestamps are in UTC ISO 8601 format
2. All monetary values are in cents/smallest currency unit
3. File uploads have a 10MB limit
4. Background tasks may take several seconds to complete
5. AI model downloads automatically on first use

---

## 🐛 Error Response Format

```json
{
  "detail": "Error message or array of validation errors",
  "message": "Human-readable error description"
}
```

For validation errors:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ],
  "message": "Validation error"
}
```
