export enum Role {
  STUDENT = 'STUDENT',
  RECRUITER = 'RECRUITER',
  PLACEMENT_OFFICER = 'PLACEMENT_OFFICER',
  ADMIN = 'ADMIN'
}

export interface User {
  id: number;
  email: string;
  role: Role;
  is_active: boolean;
}

export interface College {
  id: number;
  name: string;
  location?: string;
  website?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export enum DriveStatus {
  DRAFT = "DRAFT",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
  CLOSED = "CLOSED",
  CANCELLED = "CANCELLED"
}

export enum JobType {
  FULL_TIME = "FULL_TIME",
  INTERNSHIP = "INTERNSHIP",
  CONTRACT = "CONTRACT"
}

export interface Job {
  id: number;
  title: string;
  company_name: string;
  description?: string;
  location?: string;
  salary_package?: string;
  deadline?: string;
  drive_date?: string;
  reporting_time?: string;
  max_backlogs?: number;
  min_cgpa?: number;
  allowed_branches?: string[];
  status: DriveStatus;
  college_id: number;
  recruiter_id: number;
  created_at: string;
}

export enum ApplicationStatus {
  PENDING = "PENDING",
  REVIEWING = "REVIEWING",
  SHORTLISTED = "SHORTLISTED",
  REJECTED = "REJECTED",
  ACCEPTED = "ACCEPTED",
  WITHDRAWN = "WITHDRAWN",
  ELIGIBILITY_FAILED = "ELIGIBILITY_FAILED"
}

export interface StudentSummary {
  id: number;
  name: string;
  roll_number: string;
  branch: string;
  cgpa: number;
}

export interface RoundSummary {
  id: number;
  round_number: number;
  round_name: string;
  result: string;
}

export interface Application {
  id: number;
  student_id: number;
  job_id: number;
  resume_id?: number;
  cover_letter?: string;
  status: ApplicationStatus;
  is_eligible: boolean;
  eligibility_reasons?: string[];
  ai_score?: number;
  ai_rank?: number;
  applied_at: string;
  updated_at: string;
  student?: StudentSummary;
  job?: { id: number; title: string; company_name: string; };
  rounds?: RoundSummary[];
}
