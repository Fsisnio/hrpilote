from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime, date, timedelta
from typing import List, Optional

from beanie import PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.mongo import get_mongo_db
from app.api.v1.auth import get_current_user
from app.models.mongo_models import (
    UserDocument,
    EmployeeDocument,
    AttendanceDocument,
    AttendanceBreakDocument,
    WorkScheduleDocument,
    TimeOffRequestDocument,
)
from app.models.enums import AttendanceStatus, BreakType, AttendanceType, TimeOffStatus, UserRole
from app.schemas.attendance import (
    AttendanceCreate, AttendanceUpdate, AttendanceResponse,
    AttendanceBreakCreate, AttendanceBreakResponse,
    WorkScheduleCreate, WorkScheduleUpdate, WorkScheduleResponse,
    TimeOffRequestCreate, TimeOffRequestUpdate, TimeOffRequestResponse,
    AttendanceSummary, AttendanceReport
)

router = APIRouter()


def _attendance_to_response(attendance: AttendanceDocument) -> AttendanceResponse:
    return AttendanceResponse(
        id=str(attendance.id),
        employee_id=str(attendance.employee_id),
        organization_id=str(attendance.organization_id),
        date=attendance.date,
        clock_in_time=attendance.clock_in_time,
        clock_out_time=attendance.clock_out_time,
        expected_clock_in=attendance.expected_clock_in,
        expected_clock_out=attendance.expected_clock_out,
        total_hours=attendance.total_hours,
        regular_hours=attendance.regular_hours,
        overtime_hours=attendance.overtime_hours,
        status=attendance.status,
        attendance_type=attendance.attendance_type,
        clock_in_location=attendance.clock_in_location,
        clock_out_location=attendance.clock_out_location,
        clock_in_ip=attendance.clock_in_ip,
        clock_out_ip=attendance.clock_out_ip,
        notes=attendance.notes,
        approved_by=str(attendance.approved_by) if attendance.approved_by else None,
        approved_at=attendance.approved_at,
        is_approved=attendance.is_approved,
        created_at=attendance.created_at,
        updated_at=attendance.updated_at,
    )


def _break_to_response(break_doc: AttendanceBreakDocument) -> AttendanceBreakResponse:
    return AttendanceBreakResponse(
        id=str(break_doc.id),
        attendance_id=str(break_doc.attendance_id),
        break_type=break_doc.break_type,
        break_start=break_doc.break_start,
        break_end=break_doc.break_end,
        duration_minutes=break_doc.duration_minutes,
        location=break_doc.location,
        notes=break_doc.notes,
        created_at=break_doc.created_at,
        updated_at=break_doc.updated_at,
    )


def _schedule_to_response(schedule: WorkScheduleDocument) -> WorkScheduleResponse:
    return WorkScheduleResponse(
        id=str(schedule.id),
        organization_id=str(schedule.organization_id),
        department_id=str(schedule.department_id) if schedule.department_id else None,
        employee_id=str(schedule.employee_id) if schedule.employee_id else None,
        name=schedule.name,
        description=schedule.description,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        break_start=schedule.break_start,
        break_end=schedule.break_end,
        working_days=schedule.working_days,
        overtime_threshold_hours=schedule.overtime_threshold_hours,
        overtime_rate_multiplier=schedule.overtime_rate_multiplier,
        allow_flexible_hours=schedule.allow_flexible_hours,
        grace_period_minutes=schedule.grace_period_minutes,
        is_active=schedule.is_active,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


def _timeoff_to_response(request: TimeOffRequestDocument) -> TimeOffRequestResponse:
    return TimeOffRequestResponse(
        id=str(request.id),
        employee_id=str(request.employee_id),
        organization_id=str(request.organization_id),
        request_type=request.request_type,
        start_date=request.start_date,
        end_date=request.end_date,
        start_time=request.start_time,
        end_time=request.end_time,
        total_days=request.total_days,
        total_hours=request.total_hours,
        status=request.status.value if isinstance(request.status, TimeOffStatus) else request.status,
        reason=request.reason,
        notes=request.notes,
        rejection_reason=request.rejection_reason,
        emergency_contact_name=request.emergency_contact_name,
        emergency_contact_phone=request.emergency_contact_phone,
        handover_to=request.handover_to,
        handover_notes=request.handover_notes,
        requested_by=str(request.requested_by),
        approved_by=str(request.approved_by) if request.approved_by else None,
        approved_at=request.approved_at,
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


async def _get_employee_for_user(user: UserDocument) -> EmployeeDocument:
    employee = await EmployeeDocument.find_one(EmployeeDocument.user_id == user.id)
    if not employee:
        role = user.role.value if hasattr(user.role, "value") else user.role
        message = (
            "Employee record not found. Please contact HR to set up your employee profile."
            if role == "EMPLOYEE" else
            f"Attendance tracking is not available for {role} role. Only employees can track attendance."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if role == "EMPLOYEE" else status.HTTP_403_FORBIDDEN,
            detail=message
        )
    return employee


async def _get_today_attendance(employee: EmployeeDocument) -> Optional[AttendanceDocument]:
    return await AttendanceDocument.find_one(
        {
            "employee_id": employee.id,
            "date": date.today(),
        }
    )


async def _get_or_create_today_attendance(employee: EmployeeDocument) -> AttendanceDocument:
    attendance = await _get_today_attendance(employee)
    if not attendance:
        attendance = AttendanceDocument(
            employee_id=employee.id,
            organization_id=employee.organization_id,
            date=date.today(),
        )
        await attendance.insert()
    return attendance


async def _get_applicable_schedule(employee: EmployeeDocument) -> Optional[WorkScheduleDocument]:
    schedule = await WorkScheduleDocument.find_one(
        {
            "employee_id": employee.id,
            "is_active": True,
        }
    )
    if schedule:
        return schedule
    if employee.department_id:
        schedule = await WorkScheduleDocument.find_one(
            {
                "department_id": employee.department_id,
                "employee_id": None,
                "is_active": True,
            }
        )
        if schedule:
            return schedule
    return None


@router.post("/clock-in", response_model=AttendanceResponse)
async def clock_in(
    attendance_data: AttendanceCreate,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Clock in for the day"""
    employee = await _get_employee_for_user(current_user)

    attendance = await _get_today_attendance(employee)
    if attendance and attendance.clock_in_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already clocked in today"
        )

    attendance = attendance or await _get_or_create_today_attendance(employee)

    attendance.clock_in_time = datetime.utcnow()
    attendance.clock_in_location = attendance_data.location
    attendance.clock_in_ip = attendance_data.ip_address
    attendance.status = AttendanceStatus.PRESENT

    work_schedule = await _get_applicable_schedule(employee)
    if work_schedule:
        attendance.expected_clock_in = work_schedule.start_time
        attendance.expected_clock_out = work_schedule.end_time

    await attendance.save()
    return _attendance_to_response(attendance)


@router.post("/clock-out", response_model=AttendanceResponse)
async def clock_out(
    attendance_data: AttendanceCreate,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Clock out for the day"""
    employee = await _get_employee_for_user(current_user)
    attendance = await _get_today_attendance(employee)

    if not attendance or not attendance.clock_in_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No clock-in record found for today"
        )

    if attendance.clock_out_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already clocked out today"
        )

    attendance.clock_out_time = datetime.utcnow()
    attendance.clock_out_location = attendance_data.location
    attendance.clock_out_ip = attendance_data.ip_address

    if attendance.clock_in_time and attendance.clock_out_time:
        duration = attendance.clock_out_time - attendance.clock_in_time
        attendance.total_hours = duration.total_seconds() / 3600

        work_schedule = await _get_applicable_schedule(employee)
        if work_schedule:
            regular_hours = work_schedule.overtime_threshold_hours
            attendance.regular_hours = min(attendance.total_hours, regular_hours)
            attendance.overtime_hours = max(0, attendance.total_hours - regular_hours)
        else:
            attendance.regular_hours = attendance.total_hours

    await attendance.save()
    return _attendance_to_response(attendance)


@router.post("/break/start", response_model=AttendanceBreakResponse)
async def start_break(
    break_data: AttendanceBreakCreate,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Start a break"""
    # Get employee record
    employee = await _get_employee_for_user(current_user)
    attendance = await _get_today_attendance(employee)

    if not attendance or not attendance.clock_in_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active attendance record found"
        )
    
    # Check if already on break
    active_break = await AttendanceBreakDocument.find_one(
        {
            "attendance_id": attendance.id,
            "break_end": None,
        }
    )

    if active_break:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already on break"
        )
    
    # Create break record
    break_record = AttendanceBreakDocument(
        attendance_id=attendance.id,
        break_type=break_data.break_type,
        break_start=datetime.utcnow(),
        location=break_data.location,
        notes=break_data.notes
    )
    
    await break_record.insert()
    return _break_to_response(break_record)


@router.post("/break/end", response_model=AttendanceBreakResponse)
async def end_break(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """End current break"""
    # Get employee record
    employee = await _get_employee_for_user(current_user)
    attendance = await _get_today_attendance(employee)
    
    if not attendance or not attendance.clock_in_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active attendance record found"
        )
    
    # Get active break
    active_break = await AttendanceBreakDocument.find_one(
        {
            "attendance_id": attendance.id,
            "break_end": None,
        }
    )
    
    if not active_break:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active break found"
        )
    
    # End break
    active_break.break_end = datetime.utcnow()
    duration = active_break.break_end - active_break.break_start
    active_break.duration_minutes = int(duration.total_seconds() / 60)
    
    await active_break.save()
    return _break_to_response(active_break)


@router.get("/today", response_model=AttendanceResponse)
async def get_today_attendance(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get today's attendance record"""
    employee = await _get_employee_for_user(current_user)
    attendance = await _get_today_attendance(employee)

    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No attendance record found for today"
        )

    return _attendance_to_response(attendance)


@router.get("/history", response_model=List[AttendanceResponse])
async def get_attendance_history(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get attendance history for a date range"""
    # Check if user has employee record
    employee = await _get_employee_for_user(current_user)

    attendance_records = await AttendanceDocument.find(
        {
            "employee_id": employee.id,
            "date": {"$gte": start_date, "$lte": end_date},
        }
    ).sort("-date").to_list()
    
    return [_attendance_to_response(record) for record in attendance_records]


@router.get("/summary", response_model=AttendanceSummary)
async def get_attendance_summary(
    month: int = Query(..., description="Month (1-12)"),
    year: int = Query(..., description="Year"),
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get attendance summary for a month"""
    # Get employee record
    employee = await _get_employee_for_user(current_user)
    
    # Calculate date range
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    # Get attendance records
    attendance_records = await AttendanceDocument.find(
        {
            "employee_id": employee.id,
            "date": {"$gte": start_date, "$lte": end_date},
        }
    ).to_list()
    
    # Calculate summary
    total_days = len(attendance_records)
    present_days = len([a for a in attendance_records if a.status == AttendanceStatus.PRESENT])
    absent_days = len([a for a in attendance_records if a.status == AttendanceStatus.ABSENT])
    late_days = len([a for a in attendance_records if a.status == AttendanceStatus.LATE])
    
    total_hours = sum(a.total_hours for a in attendance_records if a.total_hours)
    regular_hours = sum(a.regular_hours for a in attendance_records if a.regular_hours)
    overtime_hours = sum(a.overtime_hours for a in attendance_records if a.overtime_hours)
    
    return AttendanceSummary(
        month=month,
        year=year,
        total_days=total_days,
        present_days=present_days,
        absent_days=absent_days,
        late_days=late_days,
        total_hours=total_hours,
        regular_hours=regular_hours,
        overtime_hours=overtime_hours
    )


# Work Schedule endpoints
@router.post("/schedules", response_model=WorkScheduleResponse)
async def create_work_schedule(
    schedule_data: WorkScheduleCreate,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Create a new work schedule"""
    # Check permissions (only HR and admins can create schedules)
    role = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role not in ["HR", "SUPER_ADMIN", "ORG_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    department_id = None
    if schedule_data.department_id:
        try:
            department_id = PydanticObjectId(schedule_data.department_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid department ID")

    employee_id = None
    if schedule_data.employee_id:
        try:
            employee_id = PydanticObjectId(schedule_data.employee_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid employee ID")

    schedule = WorkScheduleDocument(
        organization_id=current_user.organization_id,
        department_id=department_id,
        employee_id=employee_id,
        name=schedule_data.name,
        description=schedule_data.description,
        start_time=schedule_data.start_time,
        end_time=schedule_data.end_time,
        break_start=schedule_data.break_start,
        break_end=schedule_data.break_end,
        working_days=schedule_data.working_days,
        overtime_threshold_hours=schedule_data.overtime_threshold_hours,
        overtime_rate_multiplier=schedule_data.overtime_rate_multiplier,
        allow_flexible_hours=schedule_data.allow_flexible_hours,
        grace_period_minutes=schedule_data.grace_period_minutes
    )
    
    await schedule.insert()
    return _schedule_to_response(schedule)


@router.get("/schedules", response_model=List[WorkScheduleResponse])
async def get_work_schedules(
    department_id: Optional[str] = Query(None, description="Filter by department"),
    employee_id: Optional[str] = Query(None, description="Filter by employee"),
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get work schedules"""
    query: dict = {"organization_id": current_user.organization_id, "is_active": True}
    
    if department_id:
        try:
            query["department_id"] = PydanticObjectId(department_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid department ID")
    
    if employee_id:
        try:
            query["employee_id"] = PydanticObjectId(employee_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid employee ID")
    
    schedules = await WorkScheduleDocument.find(query).to_list()
    return [_schedule_to_response(schedule) for schedule in schedules]


# Time Off Request endpoints
@router.post("/time-off", response_model=TimeOffRequestResponse)
async def create_time_off_request(
    request_data: TimeOffRequestCreate,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Create a time off request"""
    employee = await _get_employee_for_user(current_user)
    
    # Calculate duration
    duration = request_data.end_date - request_data.start_date
    total_days = duration.days + 1
    
    request = TimeOffRequestDocument(
        employee_id=employee.id,
        organization_id=employee.organization_id,
        request_type=request_data.request_type,
        start_date=request_data.start_date,
        end_date=request_data.end_date,
        start_time=request_data.start_time,
        end_time=request_data.end_time,
        total_days=total_days,
        total_hours=request_data.total_hours,
        reason=request_data.reason,
        notes=request_data.notes,
        emergency_contact_name=request_data.emergency_contact_name,
        emergency_contact_phone=request_data.emergency_contact_phone,
        handover_to=request_data.handover_to,
        handover_notes=request_data.handover_notes,
        requested_by=current_user.id,
    )
    
    await request.insert()
    return _timeoff_to_response(request)


@router.get("/time-off", response_model=List[TimeOffRequestResponse])
async def get_time_off_requests(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get time off requests"""
    employee = await _get_employee_for_user(current_user)
    
    query = TimeOffRequestDocument.find(TimeOffRequestDocument.employee_id == employee.id)
    
    status_filter = status.upper() if status else None
    if status:
        try:
            status_enum = TimeOffStatus(status_filter)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
        query = query.find(TimeOffRequestDocument.status == status_enum)
    
    requests = await query.sort("-created_at").to_list()
    return [_timeoff_to_response(r) for r in requests]