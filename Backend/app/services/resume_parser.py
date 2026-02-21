import pdfplumber
import docx
import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path


class ResumeParser:
    """
    AI-powered resume parser to extract structured information from resumes.
    
    Supports PDF and DOCX formats.
    Extracts: skills, experience, education, certifications, contact info
    """
    
    def __init__(self):
        """Initialize the resume parser."""
        self.skill_keywords = self._load_skill_keywords()
    
    def _load_skill_keywords(self) -> List[str]:
        """Load common technical skills for matching."""
        # This is a simplified list. In production, use a comprehensive database.
        return [
            # Programming Languages
            "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go", 
            "rust", "swift", "kotlin", "php", "r", "scala", "perl",
            # Web Technologies
            "react", "angular", "vue", "node.js", "express", "django", "flask", 
            "fastapi", "spring", "asp.net", "html", "css", "sass", "bootstrap",
            # Databases
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra",
            "sql", "nosql", "oracle", "sqlserver",
            # Cloud & DevOps
            "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "gitlab", 
            "github actions", "terraform", "ansible",
            # Data Science & ML
            "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
            "scikit-learn", "pandas", "numpy", "opencv", "nlp", "computer vision",
            # Other
            "git", "agile", "scrum", "rest api", "graphql", "microservices",
            "ci/cd", "testing", "junit", "pytest"
        ]
    
    async def parse_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")
        
        return text
    
    async def parse_docx(self, file_path: str) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text content
        """
        text = ""
        try:
            doc = docx.Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            raise ValueError(f"Failed to parse DOCX: {str(e)}")
        
        return text
    
    async def extract_text(self, file_path: str, mime_type: str) -> str:
        """
        Extract text from resume file based on type.
        
        Args:
            file_path: Path to resume file
            mime_type: MIME type of the file
            
        Returns:
            Extracted text content
        """
        if mime_type == "application/pdf":
            return await self.parse_pdf(file_path)
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return await self.parse_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {mime_type}")
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text."""
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        match = re.search(phone_pattern, text)
        return match.group(0) if match else None
    
    def extract_skills(self, text: str) -> List[str]:
        """
        Extract technical skills from resume text.
        
        Args:
            text: Resume text content
            
        Returns:
            List of identified skills
        """
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.skill_keywords:
            if skill.lower() in text_lower:
                found_skills.append(skill.title())
        
        # Remove duplicates and sort
        return sorted(list(set(found_skills)))
    
    def extract_education(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract education information from resume.
        
        This is a simplified version. For production, use NLP models.
        """
        education = []
        
        # Common degree patterns
        degree_patterns = [
            r"(Bachelor|B\.?S\.?|B\.?A\.?|Master|M\.?S\.?|M\.?A\.?|PhD|Ph\.?D\.?|MBA)",
            r"(Computer Science|Engineering|Mathematics|Physics|Chemistry|Business)"
        ]
        
        # Look for education section
        lines = text.split('\n')
        in_education_section = False
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Detect education section
            if any(keyword in line_lower for keyword in ['education', 'academic', 'qualification']):
                in_education_section = True
                continue
            
            # Exit education section if we hit another section
            if in_education_section and any(keyword in line_lower for keyword in ['experience', 'work', 'project', 'skill']):
                in_education_section = False
            
            # Extract degree info if in education section
            if in_education_section or any(re.search(pattern, line, re.IGNORECASE) for pattern in degree_patterns):
                # Extract year (typically 4 digits)
                year_match = re.search(r'\b(19|20)\d{2}\b', line)
                year = year_match.group(0) if year_match else None
                
                if line.strip():
                    education.append({
                        "degree": line.strip(),
                        "year": year,
                        "institution": ""  # Would need more sophisticated parsing
                    })
        
        return education[:5]  # Limit to 5 entries
    
    def extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract work experience from resume.
        
        This is a simplified version. For production, use NLP models.
        """
        experience = []
        
        # Look for experience section
        lines = text.split('\n')
        in_experience_section = False
        current_job = {}
        
        for line in lines:
            line_lower = line.lower()
            
            # Detect experience section
            if any(keyword in line_lower for keyword in ['experience', 'employment', 'work history']):
                in_experience_section = True
                continue
            
            # Exit experience section
            if in_experience_section and any(keyword in line_lower for keyword in ['education', 'skill', 'project', 'certification']):
                if current_job:
                    experience.append(current_job)
                in_experience_section = False
                break
            
            if in_experience_section and line.strip():
                # Look for date ranges (e.g., "2020-2023", "Jan 2020 - Present")
                date_pattern = r'\b(19|20)\d{2}\b.*?\b(19|20)\d{2}\b|\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(19|20)\d{2}\b'
                
                if re.search(date_pattern, line):
                    # Start new job entry
                    if current_job:
                        experience.append(current_job)
                    current_job = {
                        "title": line.strip(),
                        "duration": re.search(date_pattern, line).group(0) if re.search(date_pattern, line) else ""
                    }
        
        if current_job:
            experience.append(current_job)
        
        return experience[:5]  # Limit to 5 entries
    
    async def parse_resume(self, file_path: str, mime_type: str) -> Dict[str, Any]:
        """
        Parse resume and extract structured data.
        
        Args:
            file_path: Path to resume file
            mime_type: MIME type of the file
            
        Returns:
            Dictionary containing parsed resume data
        """
        # Extract raw text
        raw_text = await self.extract_text(file_path, mime_type)
        
        # Extract structured information
        parsed_data = {
            "raw_text": raw_text,
            "contact_info": {
                "email": self.extract_email(raw_text),
                "phone": self.extract_phone(raw_text)
            },
            "skills": self.extract_skills(raw_text),
            "education": self.extract_education(raw_text),
            "experience": self.extract_experience(raw_text),
            "certifications": [],  # Would need more sophisticated parsing
            "summary": raw_text[:500] + "..." if len(raw_text) > 500 else raw_text
        }
        
        return parsed_data
