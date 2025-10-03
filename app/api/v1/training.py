from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, date

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User, UserRole
from app.models.employee import Employee
from app.models.training import (
    Course, CourseEnrollment, Assessment, AssessmentResult,
    CourseType, CourseStatus, EnrollmentStatus, AssessmentType
)
from app.schemas.training import (
    CourseCreate, CourseUpdate, CourseResponse,
    EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse, SelfEnrollmentRequest,
    AssessmentCreate, AssessmentUpdate, AssessmentResponse,
    AssessmentResultCreate, AssessmentResultUpdate, AssessmentResultResponse,
    TrainingSummary, CourseStatistics
)

router = APIRouter()

# Course endpoints
@router.get("/courses", response_model=List[CourseResponse])
async def get_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    status: Optional[CourseStatus] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all courses with optional filtering"""
    query = db.query(Course).filter(Course.organization_id == current_user.organization_id)
    
    # Apply filters
    if category:
        query = query.filter(Course.category == category)
    if status:
        query = query.filter(Course.status == status)
    if search:
        query = query.filter(
            (Course.title.ilike(f"%{search}%")) |
            (Course.description.ilike(f"%{search}%"))
        )
    
    courses = query.offset(skip).limit(limit).all()
    
    # Add enrollment count and completion rate
    result = []
    for course in courses:
        enrollment_count = db.query(CourseEnrollment).filter(
            CourseEnrollment.course_id == course.id
        ).count()
        
        completed_enrollments = db.query(CourseEnrollment).filter(
            and_(
                CourseEnrollment.course_id == course.id,
                CourseEnrollment.status == EnrollmentStatus.COMPLETED
            )
        ).count()
        
        completion_rate = (completed_enrollments / enrollment_count * 100) if enrollment_count > 0 else 0
        
        course_dict = CourseResponse.from_orm(course)
        course_dict.enrollment_count = enrollment_count
        course_dict.completion_rate = completion_rate
        result.append(course_dict)
    
    return result

@router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific course by ID"""
    course = db.query(Course).filter(
        and_(
            Course.id == course_id,
            Course.organization_id == current_user.organization_id
        )
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Add enrollment count and completion rate
    enrollment_count = db.query(CourseEnrollment).filter(
        CourseEnrollment.course_id == course.id
    ).count()
    
    completed_enrollments = db.query(CourseEnrollment).filter(
        and_(
            CourseEnrollment.course_id == course.id,
            CourseEnrollment.status == EnrollmentStatus.COMPLETED
        )
    ).count()
    
    completion_rate = (completed_enrollments / enrollment_count * 100) if enrollment_count > 0 else 0
    
    course_dict = CourseResponse.from_orm(course)
    course_dict.enrollment_count = enrollment_count
    course_dict.completion_rate = completion_rate
    
    return course_dict

@router.post("/courses", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new course"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create courses"
        )
    
    # Ensure organization_id is set
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be associated with an organization to create courses"
        )
    
    
    course = Course(
        organization_id=current_user.organization_id,
        instructor_id=current_user.id if current_user.role in [UserRole.HR, UserRole.ORG_ADMIN] else None,
        **course_data.dict()
    )
    
    db.add(course)
    db.commit()
    db.refresh(course)
    
    return CourseResponse.from_orm(course)

@router.put("/courses/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a course"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update courses"
        )
    
    course = db.query(Course).filter(
        and_(
            Course.id == course_id,
            Course.organization_id == current_user.organization_id
        )
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Update only provided fields
    update_data = course_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)
    
    db.commit()
    db.refresh(course)
    
    return CourseResponse.from_orm(course)

@router.delete("/courses/{course_id}")
async def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a course"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete courses"
        )
    
    course = db.query(Course).filter(
        and_(
            Course.id == course_id,
            Course.organization_id == current_user.organization_id
        )
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if there are enrollments
    enrollments = db.query(CourseEnrollment).filter(CourseEnrollment.course_id == course_id).count()
    if enrollments > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete course with existing enrollments"
        )
    
    db.delete(course)
    db.commit()
    
    return {"message": "Course deleted successfully"}

# Enrollment endpoints
@router.get("/enrollments", response_model=List[EnrollmentResponse])
async def get_enrollments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    course_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    status: Optional[EnrollmentStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all enrollments with optional filtering"""
    query = db.query(CourseEnrollment).join(Course).filter(
        Course.organization_id == current_user.organization_id
    )
    
    # Apply filters
    if course_id:
        query = query.filter(CourseEnrollment.course_id == course_id)
    if employee_id:
        query = query.filter(CourseEnrollment.employee_id == employee_id)
    if status:
        query = query.filter(CourseEnrollment.status == status)
    
    enrollments = query.offset(skip).limit(limit).all()
    
    # Add course and employee names
    result = []
    for enrollment in enrollments:
        course = db.query(Course).filter(Course.id == enrollment.course_id).first()
        employee = db.query(Employee).filter(Employee.id == enrollment.employee_id).first()
        
        # Create response object manually to include computed fields
        enrollment_dict = EnrollmentResponse(
            id=enrollment.id,
            organization_id=enrollment.organization_id,
            course_id=enrollment.course_id,
            employee_id=enrollment.employee_id,
            enrollment_date=enrollment.enrollment_date,
            start_date=enrollment.start_date,
            notes=enrollment.notes,
            status=enrollment.status,
            completion_date=enrollment.completion_date,
            final_score=enrollment.final_score,
            grade=enrollment.grade,
            certificate_issued=enrollment.certificate_issued,
            created_at=enrollment.created_at,
            updated_at=enrollment.updated_at,
            course_title=course.title if course else "Unknown Course",
            employee_name=f"{employee.first_name} {employee.last_name}" if employee else "Unknown Employee"
        )
        result.append(enrollment_dict)
    
    return result

@router.get("/enrollments/my-enrollments", response_model=List[EnrollmentResponse])
async def get_my_enrollments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get enrollments for the current user (employee)"""
    # Get the employee record for the current user
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found for current user")
    
    # Get enrollments for this employee
    enrollments = db.query(CourseEnrollment).join(Course).filter(
        and_(
            CourseEnrollment.employee_id == employee.id,
            Course.organization_id == current_user.organization_id
        )
    ).all()
    
    # Add course and employee names
    result = []
    for enrollment in enrollments:
        course = db.query(Course).filter(Course.id == enrollment.course_id).first()
        
        # Create response object manually to include computed fields
        enrollment_dict = EnrollmentResponse(
            id=enrollment.id,
            organization_id=enrollment.organization_id,
            course_id=enrollment.course_id,
            employee_id=enrollment.employee_id,
            enrollment_date=enrollment.enrollment_date,
            start_date=enrollment.start_date,
            notes=enrollment.notes,
            status=enrollment.status,
            completion_date=enrollment.completion_date,
            final_score=enrollment.final_score,
            grade=enrollment.grade,
            certificate_issued=enrollment.certificate_issued,
            created_at=enrollment.created_at,
            updated_at=enrollment.updated_at,
            course_title=course.title if course else "Unknown Course",
            employee_name=f"{employee.first_name} {employee.last_name}"
        )
        result.append(enrollment_dict)
    
    return result

@router.post("/enrollments", response_model=EnrollmentResponse)
async def create_enrollment(
    enrollment_data: EnrollmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new enrollment - Only HR, Managers, and Admins can enroll others"""
    # Check permissions - only HR, Managers, and Admins can enroll others
    if current_user.role == UserRole.EMPLOYEE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employees can only enroll themselves. Use /enrollments/self-enroll endpoint."
        )
    
    # Check if course exists and is active
    course = db.query(Course).filter(
        and_(
            Course.id == enrollment_data.course_id,
            Course.organization_id == current_user.organization_id,
            Course.status == CourseStatus.ACTIVE
        )
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or not active")
    
    # Check if employee exists
    employee = db.query(Employee).filter(
        and_(
            Employee.id == enrollment_data.employee_id,
            Employee.organization_id == current_user.organization_id
        )
    ).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if already enrolled
    existing_enrollment = db.query(CourseEnrollment).filter(
        and_(
            CourseEnrollment.course_id == enrollment_data.course_id,
            CourseEnrollment.employee_id == enrollment_data.employee_id
        )
    ).first()
    
    if existing_enrollment:
        raise HTTPException(status_code=400, detail="Employee already enrolled in this course")
    
    enrollment = CourseEnrollment(
        organization_id=current_user.organization_id,
        status=EnrollmentStatus.ENROLLED,
        **enrollment_data.dict()
    )
    
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    
    # Add course and employee names
    enrollment_dict = EnrollmentResponse(
        id=enrollment.id,
        organization_id=enrollment.organization_id,
        course_id=enrollment.course_id,
        employee_id=enrollment.employee_id,
        enrollment_date=enrollment.enrollment_date,
        start_date=enrollment.start_date,
        notes=enrollment.notes,
        status=enrollment.status,
        completion_date=enrollment.completion_date,
        final_score=enrollment.final_score,
        grade=enrollment.grade,
        certificate_issued=enrollment.certificate_issued,
        created_at=enrollment.created_at,
        updated_at=enrollment.updated_at,
        course_title=course.title,
        employee_name=f"{employee.first_name} {employee.last_name}"
    )
    
    return enrollment_dict

@router.post("/enrollments/self-enroll", response_model=EnrollmentResponse)
async def self_enroll(
    enrollment_data: SelfEnrollmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allow employees to enroll themselves in a course"""
    # Check if course exists and is active
    course = db.query(Course).filter(
        and_(
            Course.id == enrollment_data.course_id,
            Course.organization_id == current_user.organization_id,
            Course.status == CourseStatus.ACTIVE
        )
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or not active")
    
    # Get the employee record for the current user
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found for current user")
    
    # Check if already enrolled
    existing_enrollment = db.query(CourseEnrollment).filter(
        and_(
            CourseEnrollment.course_id == enrollment_data.course_id,
            CourseEnrollment.employee_id == employee.id
        )
    ).first()
    
    if existing_enrollment:
        raise HTTPException(status_code=400, detail="You are already enrolled in this course")
    
    # Create enrollment
    enrollment = CourseEnrollment(
        organization_id=current_user.organization_id,
        course_id=enrollment_data.course_id,
        employee_id=employee.id,
        enrollment_date=date.today(),
        start_date=date.today(),
        status=EnrollmentStatus.ENROLLED,
        notes=f"Self-enrollment by {current_user.first_name} {current_user.last_name}"
    )
    
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    
    # Add course and employee names
    enrollment_dict = EnrollmentResponse(
        id=enrollment.id,
        organization_id=enrollment.organization_id,
        course_id=enrollment.course_id,
        employee_id=enrollment.employee_id,
        enrollment_date=enrollment.enrollment_date,
        start_date=enrollment.start_date,
        notes=enrollment.notes,
        status=enrollment.status,
        completion_date=enrollment.completion_date,
        final_score=enrollment.final_score,
        grade=enrollment.grade,
        certificate_issued=enrollment.certificate_issued,
        created_at=enrollment.created_at,
        updated_at=enrollment.updated_at,
        course_title=course.title,
        employee_name=f"{employee.first_name} {employee.last_name}"
    )
    
    return enrollment_dict

@router.put("/enrollments/{enrollment_id}", response_model=EnrollmentResponse)
async def update_enrollment(
    enrollment_id: int,
    enrollment_data: EnrollmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an enrollment"""
    enrollment = db.query(CourseEnrollment).join(Course).filter(
        and_(
            CourseEnrollment.id == enrollment_id,
            Course.organization_id == current_user.organization_id
        )
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    # Update only provided fields
    update_data = enrollment_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(enrollment, field, value)
    
    db.commit()
    db.refresh(enrollment)
    
    # Add course and employee names
    course = db.query(Course).filter(Course.id == enrollment.course_id).first()
    employee = db.query(Employee).filter(Employee.id == enrollment.employee_id).first()
    
    enrollment_dict = EnrollmentResponse(
        id=enrollment.id,
        organization_id=enrollment.organization_id,
        course_id=enrollment.course_id,
        employee_id=enrollment.employee_id,
        enrollment_date=enrollment.enrollment_date,
        start_date=enrollment.start_date,
        notes=enrollment.notes,
        status=enrollment.status,
        completion_date=enrollment.completion_date,
        final_score=enrollment.final_score,
        grade=enrollment.grade,
        certificate_issued=enrollment.certificate_issued,
        created_at=enrollment.created_at,
        updated_at=enrollment.updated_at,
        course_title=course.title if course else "Unknown Course",
        employee_name=f"{employee.first_name} {employee.last_name}" if employee else "Unknown Employee"
    )
    
    return enrollment_dict

# Assessment endpoints
@router.get("/assessments", response_model=List[AssessmentResponse])
async def get_assessments(
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all assessments with optional filtering"""
    query = db.query(Assessment).join(Course).filter(
        Course.organization_id == current_user.organization_id
    )
    
    if course_id:
        query = query.filter(Assessment.course_id == course_id)
    
    assessments = query.all()
    
    # Add course title
    result = []
    for assessment in assessments:
        course = db.query(Course).filter(Course.id == assessment.course_id).first()
        assessment_dict = AssessmentResponse(
            id=assessment.id,
            course_id=assessment.course_id,
            title=assessment.title,
            description=assessment.description,
            assessment_type=assessment.assessment_type,
            total_points=assessment.total_points,
            passing_score=assessment.passing_score,
            weight_percentage=assessment.weight_percentage,
            duration_minutes=assessment.duration_minutes,
            due_date=assessment.due_date,
            instructions=assessment.instructions,
            content=assessment.content,
            allow_retakes=assessment.allow_retakes,
            max_attempts=assessment.max_attempts,
            is_required=assessment.is_required,
            is_active=assessment.is_active,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
            course_title=course.title if course else "Unknown Course"
        )
        result.append(assessment_dict)
    
    return result

@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific assessment by ID"""
    assessment = db.query(Assessment).join(Course).filter(
        and_(
            Assessment.id == assessment_id,
            Course.organization_id == current_user.organization_id
        )
    ).first()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    course = db.query(Course).filter(Course.id == assessment.course_id).first()
    assessment_dict = AssessmentResponse(
        id=assessment.id,
        course_id=assessment.course_id,
        title=assessment.title,
        description=assessment.description,
        assessment_type=assessment.assessment_type,
        total_points=assessment.total_points,
        passing_score=assessment.passing_score,
        weight_percentage=assessment.weight_percentage,
        duration_minutes=assessment.duration_minutes,
        due_date=assessment.due_date,
        instructions=assessment.instructions,
        content=assessment.content,
        allow_retakes=assessment.allow_retakes,
        max_attempts=assessment.max_attempts,
        is_required=assessment.is_required,
        is_active=assessment.is_active,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
        course_title=course.title if course else "Unknown Course"
    )
    
    return assessment_dict

@router.post("/assessments", response_model=AssessmentResponse)
async def create_assessment(
    assessment_data: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new assessment"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create assessments"
        )
    
    # Check if course exists
    course = db.query(Course).filter(
        and_(
            Course.id == assessment_data.course_id,
            Course.organization_id == current_user.organization_id
        )
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    assessment = Assessment(**assessment_data.dict())
    
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    # Add course title
    assessment_dict = AssessmentResponse(
        id=assessment.id,
        course_id=assessment.course_id,
        title=assessment.title,
        description=assessment.description,
        assessment_type=assessment.assessment_type,
        total_points=assessment.total_points,
        passing_score=assessment.passing_score,
        weight_percentage=assessment.weight_percentage,
        duration_minutes=assessment.duration_minutes,
        due_date=assessment.due_date,
        instructions=assessment.instructions,
        content=assessment.content,
        allow_retakes=assessment.allow_retakes,
        max_attempts=assessment.max_attempts,
        is_required=assessment.is_required,
        is_active=assessment.is_active,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
        course_title=course.title
    )
    
    return assessment_dict

@router.put("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
    assessment_id: int,
    assessment_data: AssessmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an assessment"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update assessments"
        )
    
    assessment = db.query(Assessment).join(Course).filter(
        and_(
            Assessment.id == assessment_id,
            Course.organization_id == current_user.organization_id
        )
    ).first()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Update only provided fields
    update_data = assessment_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assessment, field, value)
    
    db.commit()
    db.refresh(assessment)
    
    # Add course title
    course = db.query(Course).filter(Course.id == assessment.course_id).first()
    assessment_dict = AssessmentResponse(
        id=assessment.id,
        course_id=assessment.course_id,
        title=assessment.title,
        description=assessment.description,
        assessment_type=assessment.assessment_type,
        total_points=assessment.total_points,
        passing_score=assessment.passing_score,
        weight_percentage=assessment.weight_percentage,
        duration_minutes=assessment.duration_minutes,
        due_date=assessment.due_date,
        instructions=assessment.instructions,
        content=assessment.content,
        allow_retakes=assessment.allow_retakes,
        max_attempts=assessment.max_attempts,
        is_required=assessment.is_required,
        is_active=assessment.is_active,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
        course_title=course.title if course else "Unknown Course"
    )
    
    return assessment_dict

@router.delete("/assessments/{assessment_id}")
async def delete_assessment(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an assessment"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete assessments"
        )
    
    assessment = db.query(Assessment).join(Course).filter(
        and_(
            Assessment.id == assessment_id,
            Course.organization_id == current_user.organization_id
        )
    ).first()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Check if there are results
    results = db.query(AssessmentResult).filter(AssessmentResult.assessment_id == assessment_id).count()
    if results > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete assessment with existing results"
        )
    
    db.delete(assessment)
    db.commit()
    
    return {"message": "Assessment deleted successfully"}

# Assessment Result endpoints
@router.get("/assessment-results", response_model=List[AssessmentResultResponse])
async def get_assessment_results(
    assessment_id: Optional[int] = None,
    enrollment_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all assessment results with optional filtering"""
    query = db.query(AssessmentResult).join(Assessment).join(Course).filter(
        Course.organization_id == current_user.organization_id
    )
    
    if assessment_id:
        query = query.filter(AssessmentResult.assessment_id == assessment_id)
    if enrollment_id:
        query = query.filter(AssessmentResult.enrollment_id == enrollment_id)
    if employee_id:
        query = query.filter(AssessmentResult.employee_id == employee_id)
    
    results = query.all()
    
    # Add assessment and employee names
    result_list = []
    for result in results:
        assessment = db.query(Assessment).filter(Assessment.id == result.assessment_id).first()
        employee = db.query(Employee).filter(Employee.id == result.employee_id).first()
        grader = db.query(User).filter(User.id == result.graded_by).first() if result.graded_by else None
        
        result_dict = AssessmentResultResponse(
            id=result.id,
            assessment_id=result.assessment_id,
            enrollment_id=result.enrollment_id,
            employee_id=result.employee_id,
            score=result.score,
            max_score=result.max_score,
            percentage=result.percentage,
            passed=result.is_passed,
            attempt_number=result.attempt_number,
            submission_date=result.submitted_at or result.created_at,
            graded_date=result.graded_at,
            feedback=result.feedback,
            created_at=result.created_at,
            updated_at=result.updated_at,
            assessment_title=assessment.title if assessment else "Unknown Assessment",
            employee_name=f"{employee.first_name} {employee.last_name}" if employee else "Unknown Employee",
            grader_name=f"{grader.first_name} {grader.last_name}" if grader else None
        )
        result_list.append(result_dict)
    
    return result_list

@router.post("/assessment-results", response_model=AssessmentResultResponse)
async def create_assessment_result(
    result_data: AssessmentResultCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new assessment result"""
    # Check if assessment exists
    assessment = db.query(Assessment).join(Course).filter(
        and_(
            Assessment.id == result_data.assessment_id,
            Course.organization_id == current_user.organization_id
        )
    ).first()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Check if enrollment exists
    enrollment = db.query(CourseEnrollment).join(Course).filter(
        and_(
            CourseEnrollment.id == result_data.enrollment_id,
            Course.organization_id == current_user.organization_id
        )
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    # Create result
    result = AssessmentResult(
        assessment_id=result_data.assessment_id,
        enrollment_id=result_data.enrollment_id,
        employee_id=enrollment.employee_id,
        score=result_data.score,
        max_score=result_data.max_score,
        percentage=result_data.percentage,
        is_passed=result_data.passed,
        attempt_number=result_data.attempt_number,
        submitted_at=result_data.submission_date,
        graded_at=result_data.graded_date,
        feedback=result_data.feedback,
        graded_by=current_user.id if current_user.role in [UserRole.HR, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN] else None
    )
    
    db.add(result)
    db.commit()
    db.refresh(result)
    
    # Add assessment and employee names
    assessment_obj = db.query(Assessment).filter(Assessment.id == result.assessment_id).first()
    employee = db.query(Employee).filter(Employee.id == result.employee_id).first()
    grader = db.query(User).filter(User.id == result.graded_by).first() if result.graded_by else None
    
    result_dict = AssessmentResultResponse(
        id=result.id,
        assessment_id=result.assessment_id,
        enrollment_id=result.enrollment_id,
        employee_id=result.employee_id,
        score=result.score,
        max_score=result.max_score,
        percentage=result.percentage,
        passed=result.is_passed,
        attempt_number=result.attempt_number,
        submission_date=result.submitted_at or result.created_at,
        graded_date=result.graded_at,
        feedback=result.feedback,
        created_at=result.created_at,
        updated_at=result.updated_at,
        assessment_title=assessment_obj.title if assessment_obj else "Unknown Assessment",
        employee_name=f"{employee.first_name} {employee.last_name}" if employee else "Unknown Employee",
        grader_name=f"{grader.first_name} {grader.last_name}" if grader else None
    )
    
    return result_dict

@router.put("/assessment-results/{result_id}", response_model=AssessmentResultResponse)
async def update_assessment_result(
    result_id: int,
    result_data: AssessmentResultUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an assessment result"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update assessment results"
        )
    
    result = db.query(AssessmentResult).join(Assessment).join(Course).filter(
        and_(
            AssessmentResult.id == result_id,
            Course.organization_id == current_user.organization_id
        )
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Assessment result not found")
    
    # Update only provided fields
    update_data = result_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "passed":
            setattr(result, "is_passed", value)
        elif field == "submission_date":
            setattr(result, "submitted_at", value)
        else:
            setattr(result, field, value)
    
    # Update graded info
    result.graded_at = datetime.now()
    result.graded_by = current_user.id
    
    db.commit()
    db.refresh(result)
    
    # Add assessment and employee names
    assessment = db.query(Assessment).filter(Assessment.id == result.assessment_id).first()
    employee = db.query(Employee).filter(Employee.id == result.employee_id).first()
    grader = db.query(User).filter(User.id == result.graded_by).first() if result.graded_by else None
    
    result_dict = AssessmentResultResponse(
        id=result.id,
        assessment_id=result.assessment_id,
        enrollment_id=result.enrollment_id,
        employee_id=result.employee_id,
        score=result.score,
        max_score=result.max_score,
        percentage=result.percentage,
        passed=result.is_passed,
        attempt_number=result.attempt_number,
        submission_date=result.submitted_at or result.created_at,
        graded_date=result.graded_at,
        feedback=result.feedback,
        created_at=result.created_at,
        updated_at=result.updated_at,
        assessment_title=assessment.title if assessment else "Unknown Assessment",
        employee_name=f"{employee.first_name} {employee.last_name}" if employee else "Unknown Employee",
        grader_name=f"{grader.first_name} {grader.last_name}" if grader else None
    )
    
    return result_dict

# Course Statistics endpoint
@router.get("/courses/{course_id}/statistics", response_model=CourseStatistics)
async def get_course_statistics(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed statistics for a specific course"""
    # Check if course exists
    course = db.query(Course).filter(
        and_(
            Course.id == course_id,
            Course.organization_id == current_user.organization_id
        )
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get enrollment statistics
    total_enrollments = db.query(CourseEnrollment).filter(
        CourseEnrollment.course_id == course_id
    ).count()
    
    completed_enrollments = db.query(CourseEnrollment).filter(
        and_(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.status == EnrollmentStatus.COMPLETED
        )
    ).count()
    
    completion_rate = (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0
    
    # Get average score
    avg_score_result = db.query(func.avg(AssessmentResult.percentage)).join(
        AssessmentResult.assessment
    ).filter(Assessment.assessment_id == course_id).scalar()
    
    average_score = float(avg_score_result) if avg_score_result else 0.0
    
    # Calculate average completion time
    completion_times = []
    completed_enrollments_data = db.query(CourseEnrollment).filter(
        and_(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.status == EnrollmentStatus.COMPLETED,
            CourseEnrollment.completion_date.isnot(None),
            CourseEnrollment.start_date.isnot(None)
        )
    ).all()
    
    for enrollment in completed_enrollments_data:
        if enrollment.start_date and enrollment.completion_date:
            days = (enrollment.completion_date - enrollment.start_date).days
            completion_times.append(days)
    
    average_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0.0
    
    return CourseStatistics(
        course_id=course_id,
        course_title=course.title,
        total_enrollments=total_enrollments,
        completed_enrollments=completed_enrollments,
        completion_rate=completion_rate,
        average_score=average_score,
        average_completion_time_days=average_completion_time
    )

# Training summary endpoint
@router.get("/summary", response_model=TrainingSummary)
async def get_training_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get training summary statistics"""
    # Total courses
    total_courses = db.query(Course).filter(
        Course.organization_id == current_user.organization_id
    ).count()
    
    # Active courses
    active_courses = db.query(Course).filter(
        and_(
            Course.organization_id == current_user.organization_id,
            Course.status == CourseStatus.ACTIVE
        )
    ).count()
    
    # Total enrollments
    total_enrollments = db.query(CourseEnrollment).join(Course).filter(
        Course.organization_id == current_user.organization_id
    ).count()
    
    # Completed enrollments
    completed_enrollments = db.query(CourseEnrollment).join(Course).filter(
        and_(
            Course.organization_id == current_user.organization_id,
            CourseEnrollment.status == EnrollmentStatus.COMPLETED
        )
    ).count()
    
    # Completion rate
    completion_rate = (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0
    
    # Total assessments
    total_assessments = db.query(Assessment).join(Course).filter(
        Course.organization_id == current_user.organization_id
    ).count()
    
    # Average score
    avg_score_result = db.query(func.avg(AssessmentResult.percentage)).join(
        AssessmentResult.assessment
    ).join(CourseEnrollment.course).filter(
        Course.organization_id == current_user.organization_id
    ).scalar()
    
    average_score = float(avg_score_result) if avg_score_result else 0.0
    
    return TrainingSummary(
        total_courses=total_courses,
        active_courses=active_courses,
        total_enrollments=total_enrollments,
        completed_enrollments=completed_enrollments,
        completion_rate=completion_rate,
        total_assessments=total_assessments,
        average_score=average_score
    )

# Skills endpoints
@router.get("/skills", response_model=List[dict])
async def get_skills(
    category: Optional[str] = None,
    is_technical: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all skills with optional filtering"""
    from app.models.training import Skill
    
    query = db.query(Skill).filter(Skill.organization_id == current_user.organization_id)
    
    if category:
        query = query.filter(Skill.category == category)
    if is_technical is not None:
        query = query.filter(Skill.is_technical == is_technical)
    
    skills = query.all()
    
    result = []
    for skill in skills:
        skill_dict = {
            "id": skill.id,
            "name": skill.name,
            "description": skill.description,
            "category": skill.category,
            "proficiency_levels": skill.proficiency_levels,
            "is_technical": skill.is_technical,
            "is_soft_skill": skill.is_soft_skill,
            "is_active": skill.is_active,
            "created_at": skill.created_at,
            "updated_at": skill.updated_at
        }
        result.append(skill_dict)
    
    return result

@router.post("/skills", response_model=dict)
async def create_skill(
    skill_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new skill"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create skills"
        )
    
    from app.models.training import Skill
    
    skill = Skill(
        organization_id=current_user.organization_id,
        name=skill_data["name"],
        description=skill_data.get("description"),
        category=skill_data.get("category"),
        proficiency_levels=skill_data.get("proficiency_levels"),
        is_technical=skill_data.get("is_technical", False),
        is_soft_skill=skill_data.get("is_soft_skill", False)
    )
    
    db.add(skill)
    db.commit()
    db.refresh(skill)
    
    return {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description,
        "category": skill.category,
        "proficiency_levels": skill.proficiency_levels,
        "is_technical": skill.is_technical,
        "is_soft_skill": skill.is_soft_skill,
        "is_active": skill.is_active,
        "created_at": skill.created_at,
        "updated_at": skill.updated_at
    }

# Employee Skills endpoints
@router.get("/employee-skills", response_model=List[dict])
async def get_employee_skills(
    employee_id: Optional[int] = None,
    skill_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get employee skills with optional filtering"""
    from app.models.training import EmployeeSkill
    
    query = db.query(EmployeeSkill).join(Employee).filter(
        Employee.organization_id == current_user.organization_id
    )
    
    if employee_id:
        query = query.filter(EmployeeSkill.employee_id == employee_id)
    if skill_id:
        query = query.filter(EmployeeSkill.skill_id == skill_id)
    
    employee_skills = query.all()
    
    result = []
    for emp_skill in employee_skills:
        skill = db.query(Skill).filter(Skill.id == emp_skill.skill_id).first()
        employee = db.query(Employee).filter(Employee.id == emp_skill.employee_id).first()
        assessor = db.query(User).filter(User.id == emp_skill.assessed_by).first() if emp_skill.assessed_by else None
        
        skill_dict = {
            "id": emp_skill.id,
            "employee_id": emp_skill.employee_id,
            "skill_id": emp_skill.skill_id,
            "proficiency_level": emp_skill.proficiency_level,
            "years_of_experience": emp_skill.years_of_experience,
            "is_certified": emp_skill.is_certified,
            "certification_name": emp_skill.certification_name,
            "certification_date": emp_skill.certification_date,
            "certification_expiry": emp_skill.certification_expiry,
            "last_assessed": emp_skill.last_assessed,
            "assessed_by": emp_skill.assessed_by,
            "assessment_score": emp_skill.assessment_score,
            "notes": emp_skill.notes,
            "created_at": emp_skill.created_at,
            "updated_at": emp_skill.updated_at,
            "skill_name": skill.name if skill else "Unknown Skill",
            "employee_name": f"{employee.first_name} {employee.last_name}" if employee else "Unknown Employee",
            "assessor_name": f"{assessor.first_name} {assessor.last_name}" if assessor else None
        }
        result.append(skill_dict)
    
    return result

@router.post("/employee-skills", response_model=dict)
async def create_employee_skill(
    skill_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update employee skill"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage employee skills"
        )
    
    from app.models.training import EmployeeSkill, Skill
    
    # Check if skill exists
    skill = db.query(Skill).filter(
        and_(
            Skill.id == skill_data["skill_id"],
            Skill.organization_id == current_user.organization_id
        )
    ).first()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Check if employee exists
    employee = db.query(Employee).filter(
        and_(
            Employee.id == skill_data["employee_id"],
            Employee.organization_id == current_user.organization_id
        )
    ).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if employee skill already exists
    existing_skill = db.query(EmployeeSkill).filter(
        and_(
            EmployeeSkill.employee_id == skill_data["employee_id"],
            EmployeeSkill.skill_id == skill_data["skill_id"]
        )
    ).first()
    
    if existing_skill:
        # Update existing skill
        update_data = skill_data.copy()
        update_data.pop("employee_id", None)
        update_data.pop("skill_id", None)
        
        for field, value in update_data.items():
            if hasattr(existing_skill, field):
                setattr(existing_skill, field, value)
        
        existing_skill.assessed_by = current_user.id
        existing_skill.last_assessed = date.today()
        
        db.commit()
        db.refresh(existing_skill)
        emp_skill = existing_skill
    else:
        # Create new employee skill
        emp_skill = EmployeeSkill(
            employee_id=skill_data["employee_id"],
            skill_id=skill_data["skill_id"],
            proficiency_level=skill_data["proficiency_level"],
            years_of_experience=skill_data.get("years_of_experience", 0.0),
            is_certified=skill_data.get("is_certified", False),
            certification_name=skill_data.get("certification_name"),
            certification_date=skill_data.get("certification_date"),
            certification_expiry=skill_data.get("certification_expiry"),
            last_assessed=date.today(),
            assessed_by=current_user.id,
            assessment_score=skill_data.get("assessment_score", 0.0),
            notes=skill_data.get("notes")
        )
        
        db.add(emp_skill)
        db.commit()
        db.refresh(emp_skill)
    
    # Return the result
    skill_obj = db.query(Skill).filter(Skill.id == emp_skill.skill_id).first()
    employee_obj = db.query(Employee).filter(Employee.id == emp_skill.employee_id).first()
    assessor_obj = db.query(User).filter(User.id == emp_skill.assessed_by).first() if emp_skill.assessed_by else None
    
    return {
        "id": emp_skill.id,
        "employee_id": emp_skill.employee_id,
        "skill_id": emp_skill.skill_id,
        "proficiency_level": emp_skill.proficiency_level,
        "years_of_experience": emp_skill.years_of_experience,
        "is_certified": emp_skill.is_certified,
        "certification_name": emp_skill.certification_name,
        "certification_date": emp_skill.certification_date,
        "certification_expiry": emp_skill.certification_expiry,
        "last_assessed": emp_skill.last_assessed,
        "assessed_by": emp_skill.assessed_by,
        "assessment_score": emp_skill.assessment_score,
        "notes": emp_skill.notes,
        "created_at": emp_skill.created_at,
        "updated_at": emp_skill.updated_at,
        "skill_name": skill_obj.name if skill_obj else "Unknown Skill",
        "employee_name": f"{employee_obj.first_name} {employee_obj.last_name}" if employee_obj else "Unknown Employee",
        "assessor_name": f"{assessor_obj.first_name} {assessor_obj.last_name}" if assessor_obj else None
    }

# Training Session endpoints
@router.get("/sessions", response_model=List[dict])
async def get_training_sessions(
    course_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get training sessions with optional filtering"""
    from app.models.training import TrainingSession
    
    query = db.query(TrainingSession).filter(
        TrainingSession.organization_id == current_user.organization_id
    )
    
    if course_id:
        query = query.filter(TrainingSession.course_id == course_id)
    if status:
        query = query.filter(TrainingSession.status == status)
    
    sessions = query.all()
    
    result = []
    for session in sessions:
        course = db.query(Course).filter(Course.id == session.course_id).first()
        instructor = db.query(User).filter(User.id == session.instructor_id).first() if session.instructor_id else None
        
        session_dict = {
            "id": session.id,
            "course_id": session.course_id,
            "title": session.title,
            "description": session.description,
            "session_type": session.session_type,
            "start_datetime": session.start_datetime,
            "end_datetime": session.end_datetime,
            "duration_hours": session.duration_hours,
            "location": session.location,
            "room": session.room,
            "max_capacity": session.max_capacity,
            "current_enrollment": session.current_enrollment,
            "instructor_id": session.instructor_id,
            "instructor_name": session.instructor_name,
            "status": session.status,
            "is_active": session.is_active,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "course_title": course.title if course else "Unknown Course",
            "instructor_full_name": f"{instructor.first_name} {instructor.last_name}" if instructor else None
        }
        result.append(session_dict)
    
    return result

@router.post("/sessions", response_model=dict)
async def create_training_session(
    session_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new training session"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create training sessions"
        )
    
    from app.models.training import TrainingSession
    
    # Check if course exists
    course = db.query(Course).filter(
        and_(
            Course.id == session_data["course_id"],
            Course.organization_id == current_user.organization_id
        )
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    session = TrainingSession(
        organization_id=current_user.organization_id,
        course_id=session_data["course_id"],
        title=session_data["title"],
        description=session_data.get("description"),
        session_type=session_data["session_type"],
        start_datetime=session_data["start_datetime"],
        end_datetime=session_data["end_datetime"],
        duration_hours=session_data.get("duration_hours", 0.0),
        location=session_data.get("location"),
        room=session_data.get("room"),
        max_capacity=session_data.get("max_capacity", 0),
        instructor_id=session_data.get("instructor_id"),
        instructor_name=session_data.get("instructor_name")
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Return the result
    course_obj = db.query(Course).filter(Course.id == session.course_id).first()
    instructor = db.query(User).filter(User.id == session.instructor_id).first() if session.instructor_id else None
    
    return {
        "id": session.id,
        "course_id": session.course_id,
        "title": session.title,
        "description": session.description,
        "session_type": session.session_type,
        "start_datetime": session.start_datetime,
        "end_datetime": session.end_datetime,
        "duration_hours": session.duration_hours,
        "location": session.location,
        "room": session.room,
        "max_capacity": session.max_capacity,
        "current_enrollment": session.current_enrollment,
        "instructor_id": session.instructor_id,
        "instructor_name": session.instructor_name,
        "status": session.status,
        "is_active": session.is_active,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "course_title": course_obj.title if course_obj else "Unknown Course",
        "instructor_full_name": f"{instructor.first_name} {instructor.last_name}" if instructor else None
    } 