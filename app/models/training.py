from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, Enum, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from enum import Enum as PyEnum
from decimal import Decimal
from app.core.database import Base


class CourseType(PyEnum):
    ONLINE = "ONLINE"
    IN_PERSON = "IN_PERSON"
    HYBRID = "HYBRID"
    SELF_PACED = "SELF_PACED"
    INSTRUCTOR_LED = "INSTRUCTOR_LED"
    WORKSHOP = "WORKSHOP"
    SEMINAR = "SEMINAR"
    CERTIFICATION = "CERTIFICATION"


class CourseStatus(PyEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class EnrollmentStatus(PyEnum):
    PENDING = "PENDING"
    ENROLLED = "ENROLLED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DROPPED = "DROPPED"
    FAILED = "FAILED"


class AssessmentType(PyEnum):
    QUIZ = "QUIZ"
    EXAM = "EXAM"
    ASSIGNMENT = "ASSIGNMENT"
    PROJECT = "PROJECT"
    PRESENTATION = "PRESENTATION"
    PRACTICAL = "PRACTICAL"


class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Course details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    course_type = Column(Enum(CourseType), nullable=False)
    category = Column(String(100), nullable=True)
    
    # Duration and capacity
    duration_hours = Column(Float, default=0.0)
    duration_weeks = Column(Integer, default=0)
    max_enrollment = Column(Integer, default=0)
    min_enrollment = Column(Integer, default=1)
    
    # Prerequisites and requirements
    prerequisites = Column(Text, nullable=True)  # JSON array of course IDs
    requirements = Column(Text, nullable=True)
    target_audience = Column(Text, nullable=True)
    
    # Content and materials
    course_content = Column(Text, nullable=True)
    materials = Column(Text, nullable=True)  # JSON array of material URLs
    syllabus = Column(Text, nullable=True)
    
    # Instructor
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    instructor_name = Column(String(100), nullable=True)
    instructor_bio = Column(Text, nullable=True)
    
    # Cost and pricing
    cost = Column(Numeric(15, 2), default=0)
    currency = Column(String(3), default="USD")
    is_free = Column(Boolean, default=True)
    
    # Status and visibility
    status = Column(Enum(CourseStatus), default=CourseStatus.DRAFT)
    is_featured = Column(Boolean, default=False)
    is_mandatory = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
    instructor = relationship("User", foreign_keys=[instructor_id])
    enrollments = relationship("CourseEnrollment", back_populates="course", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="course", cascade="all, delete-orphan")
    sessions = relationship("TrainingSession", back_populates="course", cascade="all, delete-orphan")


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Enrollment details
    enrollment_date = Column(DateTime, default=func.now())
    start_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    status = Column(Enum(EnrollmentStatus), default=EnrollmentStatus.PENDING)
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    completed_modules = Column(Integer, default=0)
    total_modules = Column(Integer, default=0)
    
    # Assessment results
    final_score = Column(Float, default=0.0)
    grade = Column(String(10), nullable=True)
    certificate_issued = Column(Boolean, default=False)
    certificate_url = Column(String(500), nullable=True)
    
    # Approval and funding
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    funding_source = Column(String(100), nullable=True)
    cost_covered = Column(Numeric(15, 2), default=0)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="enrollments")
    employee = relationship("Employee")
    organization = relationship("Organization")
    approver = relationship("User", foreign_keys=[approved_by])
    assessments = relationship("AssessmentResult", back_populates="enrollment", cascade="all, delete-orphan")


class Assessment(Base):
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    
    # Assessment details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    assessment_type = Column(Enum(AssessmentType), nullable=False)
    
    # Scoring
    total_points = Column(Float, default=100.0)
    passing_score = Column(Float, default=70.0)
    weight_percentage = Column(Float, default=100.0)
    
    # Timing
    duration_minutes = Column(Integer, default=0)
    due_date = Column(DateTime, nullable=True)
    
    # Instructions and content
    instructions = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # JSON object with questions/requirements
    
    # Settings
    allow_retakes = Column(Boolean, default=False)
    max_attempts = Column(Integer, default=1)
    is_required = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="assessments")
    results = relationship("AssessmentResult", back_populates="assessment", cascade="all, delete-orphan")


class AssessmentResult(Base):
    __tablename__ = "assessment_results"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    enrollment_id = Column(Integer, ForeignKey("course_enrollments.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # Result details
    score = Column(Float, default=0.0)
    percentage = Column(Float, default=0.0)
    grade = Column(String(10), nullable=True)
    is_passed = Column(Boolean, default=False)
    
    # Attempt tracking
    attempt_number = Column(Integer, default=1)
    max_attempts = Column(Integer, default=1)
    
    # Submission details
    submitted_at = Column(DateTime, nullable=True)
    graded_at = Column(DateTime, nullable=True)
    graded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Feedback
    feedback = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    assessment = relationship("Assessment", back_populates="results")
    enrollment = relationship("CourseEnrollment", back_populates="assessments")
    employee = relationship("Employee")
    grader = relationship("User", foreign_keys=[graded_by])


class TrainingSession(Base):
    __tablename__ = "training_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Session details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    session_type = Column(Enum(CourseType), nullable=False)
    
    # Scheduling
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    duration_hours = Column(Float, default=0.0)
    
    # Location and capacity
    location = Column(String(200), nullable=True)
    room = Column(String(100), nullable=True)
    max_capacity = Column(Integer, default=0)
    current_enrollment = Column(Integer, default=0)
    
    # Instructor
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    instructor_name = Column(String(100), nullable=True)
    
    # Status
    status = Column(String(20), default="SCHEDULED")  # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="sessions")
    organization = relationship("Organization")
    instructor = relationship("User", foreign_keys=[instructor_id])
    attendees = relationship("SessionAttendance", back_populates="session", cascade="all, delete-orphan")


class SessionAttendance(Base):
    __tablename__ = "session_attendances"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("training_sessions.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # Attendance details
    status = Column(String(20), default="REGISTERED")  # REGISTERED, ATTENDED, NO_SHOW, CANCELLED
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    
    # Feedback
    rating = Column(Integer, nullable=True)  # 1-5 scale
    feedback = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    session = relationship("TrainingSession", back_populates="attendees")
    employee = relationship("Employee")


class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Skill details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    
    # Skill level
    proficiency_levels = Column(Text, nullable=True)  # JSON array of levels
    is_technical = Column(Boolean, default=False)
    is_soft_skill = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
    employee_skills = relationship("EmployeeSkill", back_populates="skill", cascade="all, delete-orphan")


class EmployeeSkill(Base):
    __tablename__ = "employee_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    
    # Skill level
    proficiency_level = Column(String(50), nullable=False)  # BEGINNER, INTERMEDIATE, ADVANCED, EXPERT
    years_of_experience = Column(Float, default=0.0)
    
    # Certification
    is_certified = Column(Boolean, default=False)
    certification_name = Column(String(200), nullable=True)
    certification_date = Column(Date, nullable=True)
    certification_expiry = Column(Date, nullable=True)
    
    # Assessment
    last_assessed = Column(Date, nullable=True)
    assessed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    assessment_score = Column(Float, default=0.0)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee")
    skill = relationship("Skill", back_populates="employee_skills")
    assessor = relationship("User", foreign_keys=[assessed_by]) 