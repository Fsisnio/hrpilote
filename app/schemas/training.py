from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

from app.models.enums import (
    AssessmentType,
    CourseStatus,
    CourseType,
    EnrollmentStatus,
)

# Course Schemas
class CourseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    course_type: CourseType
    category: Optional[str] = Field(None, max_length=100)
    duration_hours: float = Field(0.0, ge=0)
    duration_weeks: int = Field(0, ge=0)
    max_enrollment: int = Field(0, ge=0)
    min_enrollment: int = Field(1, ge=1)
    prerequisites: Optional[str] = None
    requirements: Optional[str] = None
    target_audience: Optional[str] = None
    course_content: Optional[str] = None
    materials: Optional[str] = None
    syllabus: Optional[str] = None
    instructor_name: Optional[str] = Field(None, max_length=100)
    instructor_bio: Optional[str] = None
    cost: Decimal = Field(0, ge=0)
    currency: str = Field("USD", max_length=3)
    is_free: bool = True
    is_featured: bool = False
    is_mandatory: bool = False

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    course_type: Optional[CourseType] = None
    category: Optional[str] = Field(None, max_length=100)
    duration_hours: Optional[float] = Field(None, ge=0)
    duration_weeks: Optional[int] = Field(None, ge=0)
    max_enrollment: Optional[int] = Field(None, ge=0)
    min_enrollment: Optional[int] = Field(None, ge=1)
    prerequisites: Optional[str] = None
    requirements: Optional[str] = None
    target_audience: Optional[str] = None
    course_content: Optional[str] = None
    materials: Optional[str] = None
    syllabus: Optional[str] = None
    instructor_name: Optional[str] = Field(None, max_length=100)
    instructor_bio: Optional[str] = None
    cost: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    is_free: Optional[bool] = None
    status: Optional[CourseStatus] = None
    is_featured: Optional[bool] = None
    is_mandatory: Optional[bool] = None

class CourseResponse(CourseBase):
    id: str
    organization_id: str
    instructor_id: Optional[str] = None
    status: CourseStatus
    created_at: datetime
    updated_at: datetime
    enrollment_count: int = 0
    completion_rate: float = 0.0

    class Config:
        from_attributes = True

# Enrollment Schemas
class EnrollmentBase(BaseModel):
    course_id: str
    employee_id: str
    enrollment_date: Optional[datetime] = None
    start_date: Optional[date] = None
    notes: Optional[str] = None

class EnrollmentCreate(EnrollmentBase):
    pass

class EnrollmentUpdate(BaseModel):
    status: Optional[EnrollmentStatus] = None
    completion_date: Optional[date] = None
    final_score: Optional[float] = Field(None, ge=0)
    grade: Optional[str] = None
    certificate_issued: Optional[bool] = None
    notes: Optional[str] = None

class EnrollmentResponse(EnrollmentBase):
    id: str
    organization_id: str
    status: EnrollmentStatus
    completion_date: Optional[date] = None
    final_score: float = 0.0
    grade: Optional[str] = None
    certificate_issued: bool = False
    created_at: datetime
    updated_at: datetime
    course_title: str
    employee_name: str

    class Config:
        from_attributes = True

class SelfEnrollmentRequest(BaseModel):
    course_id: str = Field(..., description="ID of the course to enroll in")

# Assessment Schemas
class AssessmentBase(BaseModel):
    course_id: str
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    assessment_type: AssessmentType
    total_points: float = Field(100.0, ge=0)
    passing_score: float = Field(70.0, ge=0)
    weight_percentage: float = Field(100.0, ge=0, le=100)
    duration_minutes: int = Field(0, ge=0)
    due_date: Optional[datetime] = None
    instructions: Optional[str] = None
    content: Optional[str] = None
    allow_retakes: bool = False
    max_attempts: int = Field(1, ge=1)
    is_required: bool = True

class AssessmentCreate(AssessmentBase):
    pass

class AssessmentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    assessment_type: Optional[AssessmentType] = None
    total_points: Optional[float] = Field(None, ge=0)
    passing_score: Optional[float] = Field(None, ge=0)
    weight_percentage: Optional[float] = Field(None, ge=0, le=100)
    duration_minutes: Optional[int] = Field(None, ge=0)
    due_date: Optional[datetime] = None
    instructions: Optional[str] = None
    content: Optional[str] = None
    allow_retakes: Optional[bool] = None
    max_attempts: Optional[int] = Field(None, ge=1)
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None

class AssessmentResponse(AssessmentBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    course_title: str

    class Config:
        from_attributes = True

# Assessment Result Schemas
class AssessmentResultBase(BaseModel):
    assessment_id: str
    enrollment_id: str
    score: float = Field(..., ge=0)
    max_score: float = Field(100.0, ge=0)
    percentage: float = Field(..., ge=0, le=100)
    passed: bool
    attempt_number: int = Field(1, ge=1)
    submission_date: datetime
    graded_date: Optional[datetime] = None
    feedback: Optional[str] = None

class AssessmentResultCreate(AssessmentResultBase):
    pass

class AssessmentResultUpdate(BaseModel):
    score: Optional[float] = Field(None, ge=0)
    max_score: Optional[float] = Field(None, ge=0)
    percentage: Optional[float] = Field(None, ge=0, le=100)
    passed: Optional[bool] = None
    graded_date: Optional[datetime] = None
    feedback: Optional[str] = None

class AssessmentResultResponse(AssessmentResultBase):
    id: str
    employee_id: str
    graded_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    assessment_title: str
    employee_name: str
    grader_name: Optional[str] = None

    class Config:
        from_attributes = True

# Training Summary Schemas
class TrainingSummary(BaseModel):
    total_courses: int
    active_courses: int
    total_enrollments: int
    completed_enrollments: int
    completion_rate: float
    total_assessments: int
    average_score: float

# Course Statistics
class CourseStatistics(BaseModel):
    course_id: str
    course_title: str
    total_enrollments: int
    completed_enrollments: int
    completion_rate: float
    average_score: float
    average_completion_time_days: float 