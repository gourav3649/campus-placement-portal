# Campus Placement Portal

A comprehensive, automated college placement management system rebuilt from scratch to replace manual, Excel-based workflows. The system features role-based dashboards, round-wise application tracking, offer management, automated eligibility checks, and in-app notifications.

## 🚀 Current Progress

We are currently rebuilding the portal in a structured, phase-wise approach. The foundation and core backend engines are fully built and operational.

### ✅ Completed Phases

*   **Phase 1: Auth & Base Setup (Backend)**
    *   **Architecture:** Clean FastAPI structure with SQLAlchemy async engine and PostgreSQL.
    *   **Security:** JWT-based authentication, bcrypt password hashing, and strict Role-Based Access Control (Admin, Student, Placement Officer, Recruiter).
    *   **Profiles:** Complete CRUD API endpoints for all user roles and colleges.
*   **Phase 2: Jobs & Applications (Backend)**
    *   **Job Engine:** Recruiter draft posting, placement officer verification & approval workflows.
    *   **Applications:** Student applications with built-in duplicate guards.
    *   **Eligibility Service:** Automated checks enforcing CGPA, branch, backlogs, and placement-status rules on every application.
*   **Phase 3: Rounds, Offers & Notifications (Backend)**
    *   **Rounds:** Round-wise tracking (Online Test, Tech, HR) with PENDING/PASSED/FAILED states.
    *   **Offers:** Auto-marking students as placed upon offer creation, with student Accept/Decline responses.
    *   **Notifications:** Real-time in-app alerts for drive openings, shortlistings, round results, and offer letters.
*   **Phase 1F: Auth & Base Setup (Frontend)**
    *   **Scaffold & Design:** Vite + React + TypeScript with a premium Tailwind CSS design system.
    *   **State & API:** Global Auth Context with token management and Axios interceptors for automatic 401 logouts.
    *   **Auth Pages:** Modern, dynamic Login and Registration forms built with React Hook Form and Zod validation.
    *   **Layouts:** Fully responsive Main layout with a role-based sidebar and dynamic top navigation.
*   **Phase 2F: Officer Dashboards (Excel Replacement)**
    *   **Drive Overview:** High-level dashboard showing all drives with `Applied | Eligible | Offers` stats.
    *   **Applicant Tracking Table:** A powerful data table replacing Excel.
    *   **Dynamic Filters:** Filter applicants instantly by Name, Roll No, Branch, and current Status.
    *   **Bulk Actions:** Multi-select applicants to trigger "Bulk Shortlist" or "Bulk Reject" simultaneously.
    *   **Round Management:** Expandable round history timeline per student and "Bulk Add Round" functionality.
*   **Phase 3F: Student Workflows (Frontend)**
    *   **Job Discovery:** Browsing approved drives with vivid UI and visual "Already Applied" guards.
    *   **Application Tracking:** Dedicated timeline view to monitor round-wise results (Passed/Failed) instantly.
    *   **Notifications:** Dedicated in-app bell notification dropdown tracking important timeline events.

---

## 📅 Remaining Roadmap

### ⏳ Phase 3F: Recruiter Workflows (Frontend)
*   **Drive Creation:** Recruiter form including `drive_date` and `reporting_time`.
*   **Recruiter Dashboard:** Overview of their posted drives and active applicants.

### ⏳ Phase 4F: Officer Tools & Admin (Frontend)
*   **Applicant Management:** UI to manage rounds, update applicant statuses, and record offers.
*   **Verifications:** Admin/Officer UI to toggle recruiter `is_verified` flags.
*   **Exports:** 1-click CSV export of placement statistics (Student Name, Branch, CGPA, Company, CTC).

### ⏳ Phase 4: AI Ranking & Matching (Backend Update)
*   **Demoted AI:** Transitioning the AI ranking from a blocking process to a background task.
*   **Soft Hint System:** Using `sentence-transformers` to rank students semantically, presenting the result purely as a "soft hint" column for officers alongside manual shortlisting tools.

---

## 🛠 Tech Stack

*   **Backend:** FastAPI, SQLAlchemy (Async), PostgreSQL, Pydantic, Alembic, python-jose (JWT).
*   **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Zustand, React Query, React Hook Form, Zod.
*   **AI (Upcoming):** Gemini API, HuggingFace Sentence Transformers.

## 🏃‍♂️ Running Locally

1. **Backend:**
   ```bash
   cd Backend
   .\venv\Scripts\activate
   uvicorn app.main:app --reload
   ```

2. **Frontend:**
   ```bash
   cd Frontend
   npm run dev
   ```
