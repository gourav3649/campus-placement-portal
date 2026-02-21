"""initial_multi_tenant_schema

Revision ID: 7ec691a05ef2
Revises: 
Create Date: 2026-02-19 12:52:06.825439

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '7ec691a05ef2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create custom ENUM types for PostgreSQL
    role_enum = postgresql.ENUM('STUDENT', 'RECRUITER', 'PLACEMENT_OFFICER', 'ADMIN', name='role', create_type=False)
    role_enum.create(op.get_bind(), checkfirst=True)
    
    jobtype_enum = postgresql.ENUM('FULL_TIME', 'PART_TIME', 'INTERNSHIP', 'CONTRACT', name='jobtype', create_type=False)
    jobtype_enum.create(op.get_bind(), checkfirst=True)
    
    jobstatus_enum = postgresql.ENUM('OPEN', 'CLOSED', 'DRAFT', name='jobstatus', create_type=False)
    jobstatus_enum.create(op.get_bind(), checkfirst=True)
    
    drivestatus_enum = postgresql.ENUM('DRAFT', 'APPROVED', 'REJECTED', 'CLOSED', 'CANCELLED', name='drivestatus', create_type=False)
    drivestatus_enum.create(op.get_bind(), checkfirst=True)
    
    applicationstatus_enum = postgresql.ENUM('PENDING', 'ELIGIBILITY_FAILED', 'REVIEWING', 'SHORTLISTED', 'REJECTED', 'ACCEPTED', 'WITHDRAWN', name='applicationstatus', create_type=False)
    applicationstatus_enum.create(op.get_bind(), checkfirst=True)
    
    # 1. Create colleges table (TENANT table - no dependencies)
    op.create_table(
        'colleges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('accreditation', sa.String(length=100), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('established_year', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_colleges_id'), 'colleges', ['id'], unique=False)
    op.create_index(op.f('ix_colleges_name'), 'colleges', ['name'], unique=True)
    
    # 2. Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', role_enum, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # 3. Create students table (FK to users and colleges)
    op.create_table(
        'students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('college_id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('enrollment_number', sa.String(length=50), nullable=True),
        sa.Column('university', sa.String(length=255), nullable=True),
        sa.Column('degree', sa.String(length=100), nullable=True),
        sa.Column('major', sa.String(length=100), nullable=True),
        sa.Column('branch', sa.String(length=100), nullable=True),
        sa.Column('graduation_year', sa.Integer(), nullable=True),
        sa.Column('cgpa', sa.Float(), nullable=True),
        sa.Column('has_backlogs', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_placed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('linkedin_url', sa.String(length=255), nullable=True),
        sa.Column('github_url', sa.String(length=255), nullable=True),
        sa.Column('portfolio_url', sa.String(length=255), nullable=True),
        sa.Column('skills', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['college_id'], ['colleges.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_students_id'), 'students', ['id'], unique=False)
    op.create_index(op.f('ix_students_college_id'), 'students', ['college_id'], unique=False)
    op.create_index(op.f('ix_students_enrollment_number'), 'students', ['enrollment_number'], unique=True)
    
    # 4. Create recruiters table (FK to users)
    op.create_table(
        'recruiters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('company_website', sa.String(length=255), nullable=True),
        sa.Column('company_description', sa.Text(), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('position', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('linkedin_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recruiters_id'), 'recruiters', ['id'], unique=False)
    op.create_index(op.f('ix_recruiters_company_name'), 'recruiters', ['company_name'], unique=False)
    
    # 5. Create placement_officers table (FK to users and colleges)
    op.create_table(
        'placement_officers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('college_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('designation', sa.String(length=100), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['college_id'], ['colleges.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_placement_officers_id'), 'placement_officers', ['id'], unique=False)
    op.create_index(op.f('ix_placement_officers_college_id'), 'placement_officers', ['college_id'], unique=False)
    
    # 6. Create jobs table (FK to recruiters and colleges)
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recruiter_id', sa.Integer(), nullable=False),
        sa.Column('college_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('requirements', sa.Text(), nullable=True),
        sa.Column('responsibilities', sa.Text(), nullable=True),
        sa.Column('job_type', jobtype_enum, nullable=False),
        sa.Column('status', jobstatus_enum, nullable=False, server_default='OPEN'),
        sa.Column('drive_status', drivestatus_enum, nullable=False, server_default='DRAFT'),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('is_remote', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('salary_min', sa.Float(), nullable=True),
        sa.Column('salary_max', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True, server_default='USD'),
        sa.Column('required_skills', sa.Text(), nullable=True),
        sa.Column('experience_years', sa.Integer(), nullable=True),
        sa.Column('education_level', sa.String(length=100), nullable=True),
        sa.Column('min_cgpa', sa.Float(), nullable=True),
        sa.Column('allowed_branches', sa.Text(), nullable=True),
        sa.Column('max_backlogs', sa.Integer(), nullable=True),
        sa.Column('exclude_placed_students', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('positions_available', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['recruiter_id'], ['recruiters.id'], ),
        sa.ForeignKeyConstraint(['college_id'], ['colleges.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_id'), 'jobs', ['id'], unique=False)
    op.create_index(op.f('ix_jobs_title'), 'jobs', ['title'], unique=False)
    op.create_index(op.f('ix_jobs_college_id'), 'jobs', ['college_id'], unique=False)
    
    # 7. Create resumes table (FK to students)
    op.create_table(
        'resumes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('parsed_data', sa.Text(), nullable=True),
        sa.Column('extracted_skills', sa.Text(), nullable=True),
        sa.Column('extracted_experience', sa.Text(), nullable=True),
        sa.Column('extracted_education', sa.Text(), nullable=True),
        sa.Column('extracted_certifications', sa.Text(), nullable=True),
        sa.Column('embedding_vector', sa.Text(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('parse_status', sa.String(length=50), nullable=True, server_default='pending'),
        sa.Column('parse_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resumes_id'), 'resumes', ['id'], unique=False)
    
    # 8. Create applications table (FK to students, jobs, resumes)
    op.create_table(
        'applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('resume_id', sa.Integer(), nullable=True),
        sa.Column('status', applicationstatus_enum, nullable=False, server_default='PENDING'),
        sa.Column('cover_letter', sa.Text(), nullable=True),
        sa.Column('is_eligible', sa.Boolean(), nullable=True),
        sa.Column('eligibility_reasons', sa.Text(), nullable=True),
        sa.Column('eligibility_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('match_score', sa.Float(), nullable=True),
        sa.Column('skills_match_score', sa.Float(), nullable=True),
        sa.Column('experience_match_score', sa.Float(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('rank_among_eligible', sa.Integer(), nullable=True),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('strengths', sa.Text(), nullable=True),
        sa.Column('weaknesses', sa.Text(), nullable=True),
        sa.Column('applied_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_applications_id'), 'applications', ['id'], unique=False)
    op.create_index(op.f('ix_applications_student_id'), 'applications', ['student_id'], unique=False)
    op.create_index(op.f('ix_applications_job_id'), 'applications', ['job_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order (respect FK dependencies)
    op.drop_index(op.f('ix_applications_job_id'), table_name='applications')
    op.drop_index(op.f('ix_applications_student_id'), table_name='applications')
    op.drop_index(op.f('ix_applications_id'), table_name='applications')
    op.drop_table('applications')
    
    op.drop_index(op.f('ix_resumes_id'), table_name='resumes')
    op.drop_table('resumes')
    
    op.drop_index(op.f('ix_jobs_college_id'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_title'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_id'), table_name='jobs')
    op.drop_table('jobs')
    
    op.drop_index(op.f('ix_placement_officers_college_id'), table_name='placement_officers')
    op.drop_index(op.f('ix_placement_officers_id'), table_name='placement_officers')
    op.drop_table('placement_officers')
    
    op.drop_index(op.f('ix_recruiters_company_name'), table_name='recruiters')
    op.drop_index(op.f('ix_recruiters_id'), table_name='recruiters')
    op.drop_table('recruiters')
    
    op.drop_index(op.f('ix_students_enrollment_number'), table_name='students')
    op.drop_index(op.f('ix_students_college_id'), table_name='students')
    op.drop_index(op.f('ix_students_id'), table_name='students')
    op.drop_table('students')
    
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    
    op.drop_index(op.f('ix_colleges_name'), table_name='colleges')
    op.drop_index(op.f('ix_colleges_id'), table_name='colleges')
    op.drop_table('colleges')
    
    # Drop ENUM types
    sa.Enum(name='applicationstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='drivestatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='jobstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='jobtype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='role').drop(op.get_bind(), checkfirst=True)
