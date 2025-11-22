import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.mongo import get_mongo_db
from app.api.v1.auth import get_current_user
from app.models.mongo_models import (
    CourseDocument,
    CourseEnrollmentDocument,
    AssessmentDocument,
    AssessmentResultDocument,
    EmployeeDocument,
    UserDocument,
    SkillDocument,
    EmployeeSkillDocument,
    TrainingSessionDocument,
)
from app.models.enums import (
    UserRole,
    CourseType as CourseTypeEnum,
    CourseStatus as CourseStatusEnum,
    EnrollmentStatus as EnrollmentStatusEnum,
    AssessmentType as AssessmentTypeEnum,
)
from app.schemas.training import (
    CourseCreate, CourseUpdate, CourseResponse,
    EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse, SelfEnrollmentRequest,
    AssessmentCreate, AssessmentUpdate, AssessmentResponse,
    AssessmentResultCreate, AssessmentResultUpdate, AssessmentResultResponse,
    TrainingSummary, CourseStatistics
)

router = APIRouter()
logger = logging.getLogger(__name__)

GRADER_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.ORG_ADMIN,
    UserRole.HR,
]


def _parse_object_id(value: str, label: str) -> PydanticObjectId:
    try:
        return PydanticObjectId(value)
    except Exception:
        raise HTTPException(status_code=404, detail=f"{label} not found")


def _require_org(user: UserDocument) -> PydanticObjectId:
    if not user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with an organization",
        )
    return user.organization_id


def _ensure_role(user: UserDocument, allowed_roles: List[UserRole]) -> None:
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action",
        )


# Course endpoints (Mongo)

async def _compute_enrollment_stats(course_ids: List[PydanticObjectId]) -> Dict[PydanticObjectId, Dict[str, int]]:
    stats: Dict[PydanticObjectId, Dict[str, int]] = {
        cid: {"total": 0, "completed": 0} for cid in course_ids
    }
    if not course_ids:
        return stats

    enrollments = await CourseEnrollmentDocument.find(
        {"course_id": {"$in": course_ids}}
    ).to_list()

    for enrollment in enrollments:
        entry = stats.setdefault(enrollment.course_id, {"total": 0, "completed": 0})
        entry["total"] += 1
        if enrollment.status == EnrollmentStatusEnum.COMPLETED:
            entry["completed"] += 1

    return stats


async def _require_course(course_id: str, current_user: UserDocument) -> CourseDocument:
    course_oid = _parse_object_id(course_id, "Course")
    course = await CourseDocument.get(course_oid)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    org_id = _require_org(current_user)
    if course.organization_id != org_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this course")
    return course


async def _require_assessment(assessment_id: str, current_user: UserDocument) -> AssessmentDocument:
    assessment_oid = _parse_object_id(assessment_id, "Assessment")
    assessment = await AssessmentDocument.get(assessment_oid)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    org_id = _require_org(current_user)
    if assessment.organization_id != org_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this assessment")
    return assessment


def _course_to_response(
    course: CourseDocument,
    enrollment_count: int = 0,
    completion_rate: float = 0.0,
) -> CourseResponse:
    base_fields = {
        "title",
        "description",
        "course_type",
        "category",
        "duration_hours",
        "duration_weeks",
        "max_enrollment",
        "min_enrollment",
        "prerequisites",
        "requirements",
        "target_audience",
        "course_content",
        "materials",
        "syllabus",
        "instructor_name",
        "instructor_bio",
        "cost",
        "currency",
        "is_free",
        "is_featured",
        "is_mandatory",
    }
    base_data = course.model_dump(include=base_fields)

    return CourseResponse(
        id=str(course.id),
        organization_id=str(course.organization_id),
        instructor_id=str(course.instructor_id) if course.instructor_id else None,
        status=course.status,
        created_at=course.created_at,
        updated_at=course.updated_at,
        enrollment_count=enrollment_count,
        completion_rate=completion_rate,
        **base_data,
    )


def _assessment_to_response(
    assessment: AssessmentDocument,
    course_map: Dict[PydanticObjectId, CourseDocument],
) -> AssessmentResponse:
    course = course_map.get(assessment.course_id)
    course_title = course.title if course else "Unknown Course"
    base_fields = {
        "course_id",
        "title",
        "description",
        "assessment_type",
        "total_points",
        "passing_score",
        "weight_percentage",
        "duration_minutes",
        "due_date",
        "instructions",
        "content",
        "allow_retakes",
        "max_attempts",
        "is_required",
        "is_active",
    }
    base_data = assessment.model_dump(include=base_fields)

    return AssessmentResponse(
        id=str(assessment.id),
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
        course_title=course_title,
        **base_data,
    )


@router.get("/courses", response_model=List[CourseResponse])
async def get_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    status: Optional[CourseStatusEnum] = None,
    search: Optional[str] = None,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get all courses with optional filtering."""
    org_id = _require_org(current_user)

    query: Dict[str, Any] = {"organization_id": org_id}
    if category:
        query["category"] = category
    if status:
        query["status"] = status
    if search:
        regex = {"$regex": search, "$options": "i"}
        query["$or"] = [{"title": regex}, {"description": regex}]

    courses = (
        await CourseDocument.find(query)
        .sort("-created_at")
        .skip(skip)
        .limit(limit)
        .to_list()
    )

    stats = await _compute_enrollment_stats([course.id for course in courses])
    responses: List[CourseResponse] = []
    for course in courses:
        course_stats = stats.get(course.id, {"total": 0, "completed": 0})
        completion_rate = (
            (course_stats["completed"] / course_stats["total"] * 100)
            if course_stats["total"]
            else 0.0
        )
        responses.append(
            _course_to_response(
                course,
                enrollment_count=course_stats["total"],
                completion_rate=completion_rate,
            )
        )

    return responses


@router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get a specific course by ID."""
    course = await _require_course(course_id, current_user)
    stats = await _compute_enrollment_stats([course.id])
    counts = stats.get(course.id, {"total": 0, "completed": 0})
    completion_rate = (
        (counts["completed"] / counts["total"] * 100) if counts["total"] else 0.0
    )
    return _course_to_response(course, counts["total"], completion_rate)


@router.post("/courses", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Create a new course."""
    _ensure_role(current_user, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR])
    org_id = _require_org(current_user)

    payload = course_data.model_dump()
    course = CourseDocument(
        organization_id=org_id,
        instructor_id=current_user.id if current_user.role in [UserRole.HR, UserRole.ORG_ADMIN] else None,
        **payload,
        status=CourseStatusEnum.DRAFT,
    )
    await course.insert()

    return _course_to_response(course, 0, 0.0)


@router.put("/courses/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: str,
    course_data: CourseUpdate,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Update a course."""
    _ensure_role(current_user, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR])
    course = await _require_course(course_id, current_user)

    update_data = course_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)
    course.updated_at = datetime.utcnow()
    await course.save()

    stats = await _compute_enrollment_stats([course.id])
    counts = stats.get(course.id, {"total": 0, "completed": 0})
    completion_rate = (
        (counts["completed"] / counts["total"] * 100) if counts["total"] else 0.0
    )
    return _course_to_response(course, counts["total"], completion_rate)


@router.delete("/courses/{course_id}")
async def delete_course(
    course_id: str,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Delete a course (if it has no enrollments)."""
    _ensure_role(current_user, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR])
    course = await _require_course(course_id, current_user)

    enrollments = await CourseEnrollmentDocument.find({"course_id": course.id}).count()
    if enrollments > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete course with existing enrollments",
        )

    await course.delete()
    return {"message": "Course deleted successfully"}

# Enrollment endpoints

async def _build_course_map(course_ids: List[PydanticObjectId]) -> Dict[PydanticObjectId, CourseDocument]:
    if not course_ids:
        return {}
    courses = await CourseDocument.find({"_id": {"$in": list(course_ids)}}).to_list()
    return {course.id: course for course in courses}


async def _build_employee_map(employee_ids: List[PydanticObjectId]) -> Dict[PydanticObjectId, EmployeeDocument]:
    if not employee_ids:
        return {}
    employees = await EmployeeDocument.find({"_id": {"$in": list(employee_ids)}}).to_list()
    return {employee.id: employee for employee in employees}


async def _build_assessment_map(assessment_ids: List[PydanticObjectId]) -> Dict[PydanticObjectId, AssessmentDocument]:
    if not assessment_ids:
        return {}
    assessments = await AssessmentDocument.find({"_id": {"$in": list(assessment_ids)}}).to_list()
    return {assessment.id: assessment for assessment in assessments}


async def _build_enrollment_map(enrollment_ids: List[PydanticObjectId]) -> Dict[PydanticObjectId, CourseEnrollmentDocument]:
    if not enrollment_ids:
        return {}
    enrollments = await CourseEnrollmentDocument.find({"_id": {"$in": list(enrollment_ids)}}).to_list()
    return {enrollment.id: enrollment for enrollment in enrollments}


async def _build_user_map(user_ids: List[PydanticObjectId]) -> Dict[PydanticObjectId, UserDocument]:
    if not user_ids:
        return {}
    users = await UserDocument.find({"_id": {"$in": list(user_ids)}}).to_list()
    return {user.id: user for user in users}


async def _get_employee_by_id(employee_id: str, organization_id: PydanticObjectId) -> EmployeeDocument:
    employee_oid = _parse_object_id(employee_id, "Employee")
    employee = await EmployeeDocument.get(employee_oid)
    if not employee or employee.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


async def _require_enrollment(enrollment_id: str, organization_id: PydanticObjectId) -> CourseEnrollmentDocument:
    enrollment_oid = _parse_object_id(enrollment_id, "Enrollment")
    enrollment = await CourseEnrollmentDocument.get(enrollment_oid)
    if not enrollment or enrollment.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return enrollment


async def _get_employee_for_user(current_user: UserDocument) -> EmployeeDocument:
    employee = await EmployeeDocument.find_one(EmployeeDocument.user_id == current_user.id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found for current user")
    if current_user.role != UserRole.SUPER_ADMIN and employee.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return employee


def _assessment_result_to_response(
    result: AssessmentResultDocument,
    assessment_map: Dict[PydanticObjectId, AssessmentDocument],
    employee_map: Dict[PydanticObjectId, EmployeeDocument],
    user_map: Dict[PydanticObjectId, UserDocument],
) -> AssessmentResultResponse:
    assessment = assessment_map.get(result.assessment_id)
    employee = employee_map.get(result.employee_id)
    grader = user_map.get(result.graded_by) if result.graded_by else None

    assessment_title = assessment.title if assessment else "Unknown Assessment"
    employee_name = (
        f"{employee.first_name} {employee.last_name}" if employee else "Unknown Employee"
    )
    grader_name = (
        f"{grader.first_name} {grader.last_name}" if grader else None
    )

    return AssessmentResultResponse(
        id=str(result.id),
        assessment_id=str(result.assessment_id),
        enrollment_id=str(result.enrollment_id),
        employee_id=str(result.employee_id),
        score=result.score,
        max_score=result.max_score,
        percentage=result.percentage,
        passed=result.passed,
        attempt_number=result.attempt_number,
        submission_date=result.submission_date,
        graded_date=result.graded_date,
        feedback=result.feedback,
        graded_by=str(result.graded_by) if result.graded_by else None,
        created_at=result.created_at,
        updated_at=result.updated_at,
        assessment_title=assessment_title,
        employee_name=employee_name,
        grader_name=grader_name,
    )


async def _require_assessment_result(result_id: str, current_user: UserDocument) -> AssessmentResultDocument:
    result_oid = _parse_object_id(result_id, "Assessment Result")
    result = await AssessmentResultDocument.get(result_oid)
    if not result:
        raise HTTPException(status_code=404, detail="Assessment result not found")
    org_id = _require_org(current_user)
    if result.organization_id != org_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied to this assessment result")
    return result


async def _calculate_course_average_score(course_id: PydanticObjectId) -> float:
    """
    Compute course-wide average by fetching all related assessment results.
    Aggregation queries were causing Motor cursor await errors, so we fall back
    to a simple in-memory average which is reliable for the expected dataset size.
    """
    assessments = await AssessmentDocument.find({"course_id": course_id}).to_list()
    assessment_ids = [assessment.id for assessment in assessments]
    if not assessment_ids:
        return 0.0

    results = await AssessmentResultDocument.find(
        {"assessment_id": {"$in": assessment_ids}}
    ).to_list()
    if not results:
        return 0.0

    total = sum(float(result.percentage or 0.0) for result in results)
    return total / len(results)


async def _calculate_average_completion_time_days(course_id: PydanticObjectId) -> float:
    completed_enrollments = await CourseEnrollmentDocument.find(
        {
            "course_id": course_id,
            "status": EnrollmentStatusEnum.COMPLETED,
            "start_date": {"$ne": None},
            "completion_date": {"$ne": None},
        }
    ).to_list()
    if not completed_enrollments:
        return 0.0

    completion_times = []
    for enrollment in completed_enrollments:
        if enrollment.start_date and enrollment.completion_date:
            delta = enrollment.completion_date - enrollment.start_date
            completion_times.append(delta.days)

    if not completion_times:
        return 0.0
    return sum(completion_times) / len(completion_times)


async def _calculate_org_average_score(org_id: PydanticObjectId) -> float:
    """
    Return the org-wide assessment percentage average without using aggregation
    (aggregation was breaking due to Motor cursor awaiting issues).
    """
    results = await AssessmentResultDocument.find(
        {"organization_id": org_id}
    ).to_list()
    if not results:
        return 0.0

    total = sum(float(result.percentage or 0.0) for result in results)
    return total / len(results)


async def _build_skill_map(skill_ids: List[PydanticObjectId]) -> Dict[PydanticObjectId, SkillDocument]:
    if not skill_ids:
        return {}
    skills = await SkillDocument.find({"_id": {"$in": list(skill_ids)}}).to_list()
    return {skill.id: skill for skill in skills}


async def _require_skill(skill_id: str, current_user: UserDocument) -> SkillDocument:
    skill_oid = _parse_object_id(skill_id, "Skill")
    skill = await SkillDocument.get(skill_oid)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    org_id = _require_org(current_user)
    if skill.organization_id != org_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied to this skill")
    return skill


def _skill_to_dict(skill: SkillDocument) -> Dict[str, Any]:
    return {
        "id": str(skill.id),
        "name": skill.name,
        "description": skill.description,
        "category": skill.category,
        "proficiency_levels": skill.proficiency_levels or [],
        "is_technical": skill.is_technical,
        "is_soft_skill": skill.is_soft_skill,
        "is_active": skill.is_active,
        "created_at": skill.created_at,
        "updated_at": skill.updated_at,
    }


def _parse_optional_date(value: Optional[Any], field: str) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format for {field}. Use ISO format YYYY-MM-DD",
            )
    raise HTTPException(status_code=400, detail=f"Invalid value for {field}")


def _parse_datetime_field(value: Any, field: str) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid datetime format for {field}. Use ISO 8601 format",
            )
    raise HTTPException(status_code=400, detail=f"{field} is required and must be a valid datetime")


def _employee_skill_to_dict(
    emp_skill: EmployeeSkillDocument,
    skill_map: Dict[PydanticObjectId, SkillDocument],
    employee_map: Dict[PydanticObjectId, EmployeeDocument],
    user_map: Dict[PydanticObjectId, UserDocument],
) -> Dict[str, Any]:
    skill = skill_map.get(emp_skill.skill_id)
    employee = employee_map.get(emp_skill.employee_id)
    assessor = user_map.get(emp_skill.assessed_by) if emp_skill.assessed_by else None

    return {
        "id": str(emp_skill.id),
        "employee_id": str(emp_skill.employee_id),
        "skill_id": str(emp_skill.skill_id),
        "proficiency_level": emp_skill.proficiency_level,
        "years_of_experience": emp_skill.years_of_experience,
        "is_certified": emp_skill.is_certified,
        "certification_name": emp_skill.certification_name,
        "certification_date": emp_skill.certification_date,
        "certification_expiry": emp_skill.certification_expiry,
        "last_assessed": emp_skill.last_assessed,
        "assessed_by": str(emp_skill.assessed_by) if emp_skill.assessed_by else None,
        "assessment_score": emp_skill.assessment_score,
        "notes": emp_skill.notes,
        "created_at": emp_skill.created_at,
        "updated_at": emp_skill.updated_at,
        "skill_name": skill.name if skill else "Unknown Skill",
        "employee_name": (
            f"{employee.first_name} {employee.last_name}" if employee else "Unknown Employee"
        ),
        "assessor_name": (
            f"{assessor.first_name} {assessor.last_name}" if assessor else None
        ),
    }


def _session_to_response(
    session: TrainingSessionDocument,
    course_map: Dict[PydanticObjectId, CourseDocument],
    instructor_map: Dict[PydanticObjectId, UserDocument],
) -> Dict[str, Any]:
    course = course_map.get(session.course_id)
    instructor = instructor_map.get(session.instructor_id) if session.instructor_id else None
    instructor_full_name = (
        f"{instructor.first_name} {instructor.last_name}" if instructor else None
    )

    return {
        "id": str(session.id),
        "course_id": str(session.course_id),
        "title": session.title,
        "description": session.description,
        "session_type": (
            session.session_type.value
            if isinstance(session.session_type, CourseTypeEnum)
            else session.session_type
        ),
        "start_datetime": session.start_datetime,
        "end_datetime": session.end_datetime,
        "duration_hours": session.duration_hours,
        "location": session.location,
        "room": session.room,
        "max_capacity": session.max_capacity,
        "current_enrollment": session.current_enrollment,
        "instructor_id": str(session.instructor_id) if session.instructor_id else None,
        "instructor_name": session.instructor_name,
        "status": session.status,
        "is_active": session.is_active,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "course_title": course.title if course else "Unknown Course",
        "instructor_full_name": instructor_full_name,
    }


def _enrollment_to_response(
    enrollment: CourseEnrollmentDocument,
    course_map: Dict[PydanticObjectId, CourseDocument],
    employee_map: Dict[PydanticObjectId, EmployeeDocument],
) -> EnrollmentResponse:
    course = course_map.get(enrollment.course_id)
    employee = employee_map.get(enrollment.employee_id)
    employee_name = (
        f"{employee.first_name} {employee.last_name}" if employee else "Unknown Employee"
    )
    course_title = course.title if course else "Unknown Course"
    return EnrollmentResponse(
        id=str(enrollment.id),
        organization_id=str(enrollment.organization_id),
        course_id=str(enrollment.course_id),
        employee_id=str(enrollment.employee_id),
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
        course_title=course_title,
        employee_name=employee_name,
    )


@router.get("/enrollments", response_model=List[EnrollmentResponse])
async def get_enrollments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    course_id: Optional[str] = None,
    employee_id: Optional[str] = None,
    status: Optional[EnrollmentStatusEnum] = None,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get all enrollments with optional filtering."""
    org_id = _require_org(current_user)
    query: Dict[str, Any] = {"organization_id": org_id}

    if course_id:
        query["course_id"] = _parse_object_id(course_id, "Course")
    if employee_id:
        query["employee_id"] = _parse_object_id(employee_id, "Employee")
    if status:
        query["status"] = status

    enrollments = (
        await CourseEnrollmentDocument.find(query)
        .sort("-created_at")
        .skip(skip)
        .limit(limit)
        .to_list()
    )

    course_ids = {enrollment.course_id for enrollment in enrollments}
    employee_ids = {enrollment.employee_id for enrollment in enrollments}
    course_map = await _build_course_map(list(course_ids))
    employee_map = await _build_employee_map(list(employee_ids))

    return [
        _enrollment_to_response(enrollment, course_map, employee_map)
        for enrollment in enrollments
    ]


@router.get("/enrollments/my-enrollments", response_model=List[EnrollmentResponse])
async def get_my_enrollments(
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get enrollments for the current user (employee)."""
    employee = await _get_employee_for_user(current_user)

    enrollments = await CourseEnrollmentDocument.find(
        {
            "organization_id": employee.organization_id,
            "employee_id": employee.id,
        }
    ).to_list()

    course_ids = {enrollment.course_id for enrollment in enrollments}
    course_map = await _build_course_map(list(course_ids))
    employee_map = {employee.id: employee}

    return [
        _enrollment_to_response(enrollment, course_map, employee_map)
        for enrollment in enrollments
    ]


@router.post("/enrollments", response_model=EnrollmentResponse)
async def create_enrollment(
    enrollment_data: EnrollmentCreate,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Create a new enrollment - admins/HR/Managers."""
    if current_user.role == UserRole.EMPLOYEE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employees must use the self-enroll endpoint",
        )

    org_id = _require_org(current_user)
    course = await _require_course(enrollment_data.course_id, current_user)
    if course.status != CourseStatusEnum.ACTIVE:
        raise HTTPException(status_code=400, detail="Course is not active")

    employee = await _get_employee_by_id(enrollment_data.employee_id, org_id)

    existing = await CourseEnrollmentDocument.find_one(
        {
            "course_id": course.id,
            "employee_id": employee.id,
        }
    )
    if existing:
        raise HTTPException(status_code=400, detail="Employee already enrolled in this course")

    enrollment = CourseEnrollmentDocument(
        organization_id=org_id,
        course_id=course.id,
        employee_id=employee.id,
        enrollment_date=enrollment_data.enrollment_date or datetime.utcnow(),
        start_date=enrollment_data.start_date,
        notes=enrollment_data.notes,
        status=EnrollmentStatusEnum.ENROLLED,
    )
    await enrollment.insert()

    course_map = {course.id: course}
    employee_map = {employee.id: employee}
    return _enrollment_to_response(enrollment, course_map, employee_map)


@router.post("/enrollments/self-enroll", response_model=EnrollmentResponse)
async def self_enroll(
    request: SelfEnrollmentRequest,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Allow employees to self-enroll in a course."""
    employee = await _get_employee_for_user(current_user)
    course = await _require_course(request.course_id, current_user)

    if course.status != CourseStatusEnum.ACTIVE:
        raise HTTPException(status_code=400, detail="Course is not active")

    existing = await CourseEnrollmentDocument.find_one(
        {
            "course_id": course.id,
            "employee_id": employee.id,
        }
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")

    enrollment = CourseEnrollmentDocument(
        organization_id=employee.organization_id,
        course_id=course.id,
        employee_id=employee.id,
        enrollment_date=datetime.utcnow(),
        status=EnrollmentStatusEnum.PENDING,
    )
    await enrollment.insert()

    course_map = {course.id: course}
    employee_map = {employee.id: employee}
    return _enrollment_to_response(enrollment, course_map, employee_map)


@router.put("/enrollments/{enrollment_id}", response_model=EnrollmentResponse)
async def update_enrollment(
    enrollment_id: str,
    enrollment_data: EnrollmentUpdate,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Update an enrollment."""
    _ensure_role(current_user, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER])
    enrollment_oid = _parse_object_id(enrollment_id, "Enrollment")
    enrollment = await CourseEnrollmentDocument.get(enrollment_oid)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    org_id = _require_org(current_user)
    if enrollment.organization_id != org_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied to this enrollment")

    update_data = enrollment_data.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"]:
        update_data["status"] = update_data["status"]

    for field, value in update_data.items():
        setattr(enrollment, field, value)

    enrollment.updated_at = datetime.utcnow()
    await enrollment.save()

    course_map = await _build_course_map([enrollment.course_id])
    employee_map = await _build_employee_map([enrollment.employee_id])
    return _enrollment_to_response(enrollment, course_map, employee_map)


@router.delete("/enrollments/{enrollment_id}")
async def delete_enrollment(
    enrollment_id: str,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Delete an enrollment."""
    _ensure_role(current_user, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER])
    enrollment_oid = _parse_object_id(enrollment_id, "Enrollment")
    enrollment = await CourseEnrollmentDocument.get(enrollment_oid)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    org_id = _require_org(current_user)
    if enrollment.organization_id != org_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied to this enrollment")

    await enrollment.delete()
    return {"message": "Enrollment deleted successfully"}
@router.get("/assessments", response_model=List[AssessmentResponse])
async def get_assessments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    course_id: Optional[str] = None,
    assessment_type: Optional[AssessmentTypeEnum] = None,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get assessments with optional filtering."""
    org_id = _require_org(current_user)
    query: Dict[str, Any] = {"organization_id": org_id}

    if course_id:
        query["course_id"] = _parse_object_id(course_id, "Course")
    if assessment_type:
        query["assessment_type"] = assessment_type

    assessments = (
        await AssessmentDocument.find(query)
        .sort("-created_at")
        .skip(skip)
        .limit(limit)
        .to_list()
    )
    course_ids = {assessment.course_id for assessment in assessments}
    course_map = await _build_course_map(list(course_ids))

    return [
        _assessment_to_response(assessment, course_map)
        for assessment in assessments
    ]

@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: str,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get a specific assessment by ID."""
    assessment_oid = _parse_object_id(assessment_id, "Assessment")
    assessment = await AssessmentDocument.get(assessment_oid)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    org_id = _require_org(current_user)
    if assessment.organization_id != org_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied to this assessment")

    course_map = await _build_course_map([assessment.course_id])
    return _assessment_to_response(assessment, course_map)

@router.post("/assessments", response_model=AssessmentResponse)
async def create_assessment(
    assessment_data: AssessmentCreate,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Create a new assessment."""
    _ensure_role(current_user, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR])
    course = await _require_course(assessment_data.course_id, current_user)

    payload = assessment_data.model_dump()
    assessment = AssessmentDocument(
        organization_id=course.organization_id,
        course_id=course.id,
        **payload,
        is_active=True,
    )
    await assessment.insert()

    return _assessment_to_response(assessment, {course.id: course})

@router.put("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
    assessment_id: str,
    assessment_data: AssessmentUpdate,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Update an assessment."""
    _ensure_role(current_user, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR])
    assessment_oid = _parse_object_id(assessment_id, "Assessment")
    assessment = await AssessmentDocument.get(assessment_oid)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    org_id = _require_org(current_user)
    if assessment.organization_id != org_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied to this assessment")

    update_data = assessment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assessment, field, value)

    assessment.updated_at = datetime.utcnow()
    await assessment.save()

    course_map = await _build_course_map([assessment.course_id])
    return _assessment_to_response(assessment, course_map)

@router.delete("/assessments/{assessment_id}")
async def delete_assessment(
    assessment_id: str,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Delete an assessment."""
    _ensure_role(current_user, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR])
    assessment_oid = _parse_object_id(assessment_id, "Assessment")
    assessment = await AssessmentDocument.get(assessment_oid)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    org_id = _require_org(current_user)
    if assessment.organization_id != org_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied to this assessment")

    result_exists = await AssessmentResultDocument.find(
        {"assessment_id": assessment.id}
    ).count()
    if result_exists > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete assessment with existing results",
        )

    await assessment.delete()
    return {"message": "Assessment deleted successfully"}

# Assessment Result endpoints
@router.get("/assessment-results", response_model=List[AssessmentResultResponse])
async def get_assessment_results(
    assessment_id: Optional[str] = None,
    enrollment_id: Optional[str] = None,
    employee_id: Optional[str] = None,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get all assessment results with optional filtering"""
    org_id = _require_org(current_user)
    query: Dict[str, Any] = {"organization_id": org_id}

    if assessment_id:
        query["assessment_id"] = _parse_object_id(assessment_id, "Assessment")
    if enrollment_id:
        query["enrollment_id"] = _parse_object_id(enrollment_id, "Enrollment")
    if employee_id:
        query["employee_id"] = _parse_object_id(employee_id, "Employee")

    results = (
        await AssessmentResultDocument.find(query)
        .sort("-created_at")
        .to_list()
    )

    if not results:
        return []

    assessment_ids = {result.assessment_id for result in results}
    employee_ids = {result.employee_id for result in results}
    grader_ids = {result.graded_by for result in results if result.graded_by}

    assessment_map = await _build_assessment_map(list(assessment_ids))
    employee_map = await _build_employee_map(list(employee_ids))
    user_map = await _build_user_map(list(grader_ids))

    return [
        _assessment_result_to_response(result, assessment_map, employee_map, user_map)
        for result in results
    ]


@router.post("/assessment-results", response_model=AssessmentResultResponse)
async def create_assessment_result(
    result_data: AssessmentResultCreate,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Create a new assessment result"""
    assessment = await _require_assessment(result_data.assessment_id, current_user)
    enrollment = await _require_enrollment(result_data.enrollment_id, assessment.organization_id)
    employee = await EmployeeDocument.get(enrollment.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    result = AssessmentResultDocument(
        organization_id=assessment.organization_id,
        assessment_id=assessment.id,
        enrollment_id=enrollment.id,
        employee_id=employee.id,
        score=result_data.score,
        max_score=result_data.max_score,
        percentage=result_data.percentage,
        passed=result_data.passed,
        attempt_number=result_data.attempt_number,
        submission_date=result_data.submission_date,
        graded_date=result_data.graded_date,
        feedback=result_data.feedback,
        graded_by=current_user.id if current_user.role in GRADER_ROLES else None,
    )

    await result.insert()

    assessment_map = {assessment.id: assessment}
    employee_map = {employee.id: employee}
    user_map = {}
    if result.graded_by:
        user_map = await _build_user_map([result.graded_by])

    return _assessment_result_to_response(result, assessment_map, employee_map, user_map)


@router.put("/assessment-results/{result_id}", response_model=AssessmentResultResponse)
async def update_assessment_result(
    result_id: str,
    result_data: AssessmentResultUpdate,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Update an assessment result"""
    _ensure_role(current_user, GRADER_ROLES)
    result = await _require_assessment_result(result_id, current_user)

    update_data = result_data.model_dump(exclude_unset=True)
    graded_date_override = update_data.pop("graded_date", None)

    for field, value in update_data.items():
        if field == "passed":
            setattr(result, "passed", value)
        else:
            setattr(result, field, value)

    result.graded_date = graded_date_override or datetime.utcnow()
    result.graded_by = current_user.id
    result.updated_at = datetime.utcnow()

    await result.save()

    assessment_map = await _build_assessment_map([result.assessment_id])
    employee_map = await _build_employee_map([result.employee_id])
    user_map = await _build_user_map([result.graded_by]) if result.graded_by else {}

    return _assessment_result_to_response(result, assessment_map, employee_map, user_map)

# Course Statistics endpoint
@router.get("/courses/{course_id}/statistics", response_model=CourseStatistics)
async def get_course_statistics(
    course_id: str,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get detailed statistics for a specific course"""
    course = await _require_course(course_id, current_user)

    total_enrollments = await CourseEnrollmentDocument.find(
        {"course_id": course.id}
    ).count()

    completed_enrollments = await CourseEnrollmentDocument.find(
        {
            "course_id": course.id,
            "status": EnrollmentStatusEnum.COMPLETED,
        }
    ).count()

    completion_rate = (
        (completed_enrollments / total_enrollments) * 100 if total_enrollments else 0.0
    )

    average_score = await _calculate_course_average_score(course.id)
    average_completion_time = await _calculate_average_completion_time_days(course.id)

    return CourseStatistics(
        course_id=str(course.id),
        course_title=course.title,
        total_enrollments=total_enrollments,
        completed_enrollments=completed_enrollments,
        completion_rate=completion_rate,
        average_score=average_score,
        average_completion_time_days=average_completion_time,
    )

# Training summary endpoint
@router.get("/summary", response_model=TrainingSummary)
async def get_training_summary(
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get training summary statistics"""
    org_id = _require_org(current_user)

    total_courses = await CourseDocument.find({"organization_id": org_id}).count()
    active_courses = await CourseDocument.find(
        {"organization_id": org_id, "status": CourseStatusEnum.ACTIVE}
    ).count()

    total_enrollments = await CourseEnrollmentDocument.find(
        {"organization_id": org_id}
    ).count()
    completed_enrollments = await CourseEnrollmentDocument.find(
        {"organization_id": org_id, "status": EnrollmentStatusEnum.COMPLETED}
    ).count()
    completion_rate = (
        (completed_enrollments / total_enrollments) * 100 if total_enrollments else 0.0
    )

    total_assessments = await AssessmentDocument.find(
        {"organization_id": org_id}
    ).count()
    average_score = await _calculate_org_average_score(org_id)

    return TrainingSummary(
        total_courses=total_courses,
        active_courses=active_courses,
        total_enrollments=total_enrollments,
        completed_enrollments=completed_enrollments,
        completion_rate=completion_rate,
        total_assessments=total_assessments,
        average_score=average_score,
    )

# Skills endpoints
@router.get("/skills", response_model=List[dict])
async def get_skills(
    category: Optional[str] = None,
    is_technical: Optional[bool] = None,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get all skills with optional filtering"""
    org_id = _require_org(current_user)
    query: Dict[str, Any] = {"organization_id": org_id}
    if category:
        query["category"] = category
    if is_technical is not None:
        query["is_technical"] = is_technical

    skills = (
        await SkillDocument.find(query)
        .sort("name")
        .to_list()
    )
    return [_skill_to_dict(skill) for skill in skills]


@router.post("/skills", response_model=dict)
async def create_skill(
    skill_data: dict,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Create a new skill"""
    _ensure_role(current_user, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR])
    if "name" not in skill_data or not skill_data["name"]:
        raise HTTPException(status_code=400, detail="Skill name is required")

    org_id = _require_org(current_user)
    proficiency_levels = skill_data.get("proficiency_levels")
    if isinstance(proficiency_levels, str):
        # Support comma-separated lists
        proficiency_levels = [level.strip() for level in proficiency_levels.split(",") if level.strip()]

    skill = SkillDocument(
        organization_id=org_id,
        name=skill_data["name"],
        description=skill_data.get("description"),
        category=skill_data.get("category"),
        proficiency_levels=proficiency_levels,
        is_technical=skill_data.get("is_technical", False),
        is_soft_skill=skill_data.get("is_soft_skill", False),
        is_active=skill_data.get("is_active", True),
    )
    await skill.insert()

    return _skill_to_dict(skill)

# Employee Skills endpoints
@router.get("/employee-skills", response_model=List[dict])
async def get_employee_skills(
    employee_id: Optional[str] = None,
    skill_id: Optional[str] = None,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get employee skills with optional filtering"""
    org_id = _require_org(current_user)
    query: Dict[str, Any] = {"organization_id": org_id}
    if employee_id:
        query["employee_id"] = _parse_object_id(employee_id, "Employee")
    if skill_id:
        query["skill_id"] = _parse_object_id(skill_id, "Skill")

    employee_skills = await EmployeeSkillDocument.find(query).to_list()

    skill_ids = {emp_skill.skill_id for emp_skill in employee_skills}
    employee_ids = {emp_skill.employee_id for emp_skill in employee_skills}
    assessor_ids = {emp_skill.assessed_by for emp_skill in employee_skills if emp_skill.assessed_by}

    skill_map = await _build_skill_map(list(skill_ids))
    employee_map = await _build_employee_map(list(employee_ids))
    user_map = await _build_user_map(list(assessor_ids))

    return [
        _employee_skill_to_dict(emp_skill, skill_map, employee_map, user_map)
        for emp_skill in employee_skills
    ]


@router.post("/employee-skills", response_model=dict)
async def create_employee_skill(
    skill_data: dict,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Create or update employee skill"""
    _ensure_role(current_user, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR])
    org_id = _require_org(current_user)

    skill_id_raw = skill_data.get("skill_id")
    employee_id_raw = skill_data.get("employee_id")
    if not skill_id_raw or not employee_id_raw:
        raise HTTPException(status_code=400, detail="skill_id and employee_id are required")

    skill = await _require_skill(str(skill_id_raw), current_user)
    employee = await _get_employee_by_id(str(employee_id_raw), org_id)

    proficiency_level = skill_data.get("proficiency_level")
    if not proficiency_level:
        raise HTTPException(status_code=400, detail="proficiency_level is required")

    certification_date = _parse_optional_date(
        skill_data.get("certification_date"), "certification_date"
    )
    certification_expiry = _parse_optional_date(
        skill_data.get("certification_expiry"), "certification_expiry"
    )

    existing_skill = await EmployeeSkillDocument.find_one(
        {
            "organization_id": org_id,
            "employee_id": employee.id,
            "skill_id": skill.id,
        }
    )

    payload = {
        "proficiency_level": proficiency_level,
        "years_of_experience": float(skill_data.get("years_of_experience", 0.0)),
        "is_certified": skill_data.get("is_certified", False),
        "certification_name": skill_data.get("certification_name"),
        "certification_date": certification_date,
        "certification_expiry": certification_expiry,
        "assessment_score": float(skill_data.get("assessment_score", 0.0)),
        "notes": skill_data.get("notes"),
    }

    if existing_skill:
        for field, value in payload.items():
            setattr(existing_skill, field, value)
        existing_skill.assessed_by = current_user.id
        existing_skill.last_assessed = date.today()
        existing_skill.updated_at = datetime.utcnow()
        await existing_skill.save()
        emp_skill = existing_skill
    else:
        emp_skill = EmployeeSkillDocument(
            organization_id=org_id,
            employee_id=employee.id,
            skill_id=skill.id,
            last_assessed=date.today(),
            assessed_by=current_user.id,
            **payload,
        )
        await emp_skill.insert()

    skill_map = {skill.id: skill}
    employee_map = {employee.id: employee}
    user_map = await _build_user_map([current_user.id])

    return _employee_skill_to_dict(emp_skill, skill_map, employee_map, user_map)

# Training Session endpoints
@router.get("/sessions", response_model=List[dict])
async def get_training_sessions(
    course_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get training sessions with optional filtering"""
    org_id = _require_org(current_user)
    query: Dict[str, Any] = {"organization_id": org_id}
    if course_id:
        query["course_id"] = _parse_object_id(course_id, "Course")
    if status:
        query["status"] = status

    sessions = (
        await TrainingSessionDocument.find(query)
        .sort("start_datetime")
        .to_list()
    )

    course_ids = {session.course_id for session in sessions}
    instructor_ids = {session.instructor_id for session in sessions if session.instructor_id}

    course_map = await _build_course_map(list(course_ids))
    instructor_map = await _build_user_map(list(instructor_ids))

    return [
        _session_to_response(session, course_map, instructor_map)
        for session in sessions
    ]


@router.post("/sessions", response_model=dict)
async def create_training_session(
    session_data: dict,
    current_user: UserDocument = Depends(get_current_user),
    _db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Create a new training session"""
    _ensure_role(current_user, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR])
    if "course_id" not in session_data or "title" not in session_data:
        raise HTTPException(status_code=400, detail="course_id and title are required")

    course = await _require_course(str(session_data["course_id"]), current_user)

    session_type_raw = session_data.get("session_type", CourseTypeEnum.ONLINE)
    try:
        session_type = (
            session_type_raw
            if isinstance(session_type_raw, CourseTypeEnum)
            else CourseTypeEnum(session_type_raw)
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_type value")

    start_datetime = _parse_datetime_field(session_data.get("start_datetime"), "start_datetime")
    end_datetime = _parse_datetime_field(session_data.get("end_datetime"), "end_datetime")

    instructor_id = session_data.get("instructor_id")
    instructor_doc: Optional[UserDocument] = None
    instructor_oid: Optional[PydanticObjectId] = None
    if instructor_id:
        instructor_oid = _parse_object_id(str(instructor_id), "Instructor")
        instructor_doc = await UserDocument.get(instructor_oid)
        if not instructor_doc:
            raise HTTPException(status_code=404, detail="Instructor not found")
        if (
            instructor_doc.organization_id != course.organization_id
            and current_user.role != UserRole.SUPER_ADMIN
        ):
            raise HTTPException(status_code=403, detail="Instructor not in this organization")

    session = TrainingSessionDocument(
        organization_id=course.organization_id,
        course_id=course.id,
        title=session_data["title"],
        description=session_data.get("description"),
        session_type=session_type,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        duration_hours=float(session_data.get("duration_hours", 0.0)),
        location=session_data.get("location"),
        room=session_data.get("room"),
        max_capacity=int(session_data.get("max_capacity", 0)),
        current_enrollment=int(session_data.get("current_enrollment", 0)),
        instructor_id=instructor_oid,
        instructor_name=session_data.get("instructor_name"),
        status=session_data.get("status", "SCHEDULED"),
        is_active=session_data.get("is_active", True),
    )
    await session.insert()

    course_map = {course.id: course}
    instructor_map = {instructor_oid: instructor_doc} if instructor_doc and instructor_oid else {}

    return _session_to_response(session, course_map, instructor_map)