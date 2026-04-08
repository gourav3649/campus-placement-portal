import enum


class Role(str, enum.Enum):
    ADMIN = "admin"
    STUDENT = "student"
    RECRUITER = "recruiter"
    PLACEMENT_OFFICER = "placement_officer"
