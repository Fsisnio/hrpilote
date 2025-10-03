from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, date, timedelta
from typing import List, Optional
from decimal import Decimal

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.attendance import (
    Attendance, AttendanceType, AttendanceStatus, BreakType,
    AttendanceBreak, WorkSchedule, TimeOffRequest
)
from app.models.employee import Employee
from app.schemas.attendance import (
    AttendanceCreate, AttendanceUpdate, AttendanceResponse,
    AttendanceBreakCreate, AttendanceBreakResponse,
    WorkScheduleCreate, WorkScheduleUpdate, WorkScheduleResponse,
    TimeOffRequestCreate, TimeOffRequestUpdate, TimeOffRequestResponse,
    AttendanceSummary, AttendanceReport
)

router = APIRouter()


@router.post("/clock-in", response_model=AttendanceResponse)
async def clock_in(
    attendance_data: AttendanceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clock in for the day"""
    # Get employee record
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee record not found"
        )
    
    # Check if already clocked in today
    today = date.today()
    existing_attendance = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == employee.id,
            Attendance.date == today
        )
    ).first()
    
    if existing_attendance and existing_attendance.clock_in_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already clocked in today"
        )
    
    # Create or update attendance record
    if existing_attendance:
        attendance = existing_attendance
    else:
        attendance = Attendance(
            employee_id=employee.id,
            organization_id=employee.organization_id,
            date=today
        )
        db.add(attendance)
    
    # Set clock in time
    attendance.clock_in_time = datetime.now()
    attendance.clock_in_location = attendance_data.location
    attendance.clock_in_ip = attendance_data.ip_address
    attendance.status = AttendanceStatus.PRESENT
    
    # Get work schedule for expected times
    work_schedule = db.query(WorkSchedule).filter(
        or_(
            WorkSchedule.employee_id == employee.id,
            and_(
                WorkSchedule.department_id == employee.department_id,
                WorkSchedule.employee_id.is_(None)
            )
        )
    ).first()
    
    if work_schedule:
        attendance.expected_clock_in = work_schedule.start_time
        attendance.expected_clock_out = work_schedule.end_time
    
    db.commit()
    db.refresh(attendance)
    
    return attendance


@router.post("/clock-out", response_model=AttendanceResponse)
async def clock_out(
    attendance_data: AttendanceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clock out for the day"""
    # Get employee record
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee record not found"
        )
    
    # Get today's attendance record
    today = date.today()
    attendance = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == employee.id,
            Attendance.date == today
        )
    ).first()
    
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
    
    # Set clock out time
    attendance.clock_out_time = datetime.now()
    attendance.clock_out_location = attendance_data.location
    attendance.clock_out_ip = attendance_data.ip_address
    
    # Calculate work hours
    if attendance.clock_in_time and attendance.clock_out_time:
        duration = attendance.clock_out_time - attendance.clock_in_time
        attendance.total_hours = duration.total_seconds() / 3600
        
        # Calculate regular and overtime hours
        work_schedule = db.query(WorkSchedule).filter(
            or_(
                WorkSchedule.employee_id == employee.id,
                and_(
                    WorkSchedule.department_id == employee.department_id,
                    WorkSchedule.employee_id.is_(None)
                )
            )
        ).first()
        
        if work_schedule:
            regular_hours = work_schedule.overtime_threshold_hours
            attendance.regular_hours = min(attendance.total_hours, regular_hours)
            attendance.overtime_hours = max(0, attendance.total_hours - regular_hours)
        else:
            attendance.regular_hours = attendance.total_hours
    
    db.commit()
    db.refresh(attendance)
    
    return attendance


@router.post("/break/start", response_model=AttendanceBreakResponse)
async def start_break(
    break_data: AttendanceBreakCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a break"""
    # Get employee record
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee record not found"
        )
    
    # Get today's attendance record
    today = date.today()
    attendance = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == employee.id,
            Attendance.date == today
        )
    ).first()
    
    if not attendance or not attendance.clock_in_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active attendance record found"
        )
    
    # Check if already on break
    active_break = db.query(AttendanceBreak).filter(
        and_(
            AttendanceBreak.attendance_id == attendance.id,
            AttendanceBreak.break_end.is_(None)
        )
    ).first()
    
    if active_break:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already on break"
        )
    
    # Create break record
    break_record = AttendanceBreak(
        attendance_id=attendance.id,
        break_type=break_data.break_type,
        break_start=datetime.now(),
        location=break_data.location,
        notes=break_data.notes
    )
    
    db.add(break_record)
    db.commit()
    db.refresh(break_record)
    
    return break_record


@router.post("/break/end", response_model=AttendanceBreakResponse)
async def end_break(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End current break"""
    # Get employee record
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee record not found"
        )
    
    # Get today's attendance record
    today = date.today()
    attendance = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == employee.id,
            Attendance.date == today
        )
    ).first()
    
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active attendance record found"
        )
    
    # Get active break
    active_break = db.query(AttendanceBreak).filter(
        and_(
            AttendanceBreak.attendance_id == attendance.id,
            AttendanceBreak.break_end.is_(None)
        )
    ).first()
    
    if not active_break:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active break found"
        )
    
    # End break
    active_break.break_end = datetime.now()
    duration = active_break.break_end - active_break.break_start
    active_break.duration_minutes = int(duration.total_seconds() / 60)
    
    db.commit()
    db.refresh(active_break)
    
    return active_break


@router.get("/today", response_model=AttendanceResponse)
async def get_today_attendance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's attendance record"""
    # Check if user has employee record
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        # Provide more helpful error message for users with EMPLOYEE role but no employee record
        if current_user.role.value == "EMPLOYEE":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee record not found. Please contact HR to set up your employee profile."
            )
        else:
            # For non-employee users (admins, etc.), return appropriate response
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Attendance tracking is not available for {current_user.role.value} role. Only employees can track attendance."
            )
    
    # Get today's attendance
    today = date.today()
    attendance = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == employee.id,
            Attendance.date == today
        )
    ).first()
    
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No attendance record found for today"
        )
    
    return attendance


@router.get("/history", response_model=List[AttendanceResponse])
async def get_attendance_history(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get attendance history for a date range"""
    # Check if user has employee record
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        # Provide more helpful error message for users with EMPLOYEE role but no employee record
        if current_user.role.value == "EMPLOYEE":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee record not found. Please contact HR to set up your employee profile."
            )
        else:
            # For non-employee users (admins, etc.), return appropriate response
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Attendance tracking is not available for {current_user.role.value} role. Only employees can track attendance."
            )
    
    # Get attendance records
    attendance_records = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == employee.id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        )
    ).order_by(Attendance.date.desc()).all()
    
    return attendance_records


@router.get("/summary", response_model=AttendanceSummary)
async def get_attendance_summary(
    month: int = Query(..., description="Month (1-12)"),
    year: int = Query(..., description="Year"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get attendance summary for a month"""
    # Get employee record
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee record not found"
        )
    
    # Calculate date range
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    # Get attendance records
    attendance_records = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == employee.id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        )
    ).all()
    
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new work schedule"""
    # Check permissions (only HR and admins can create schedules)
    if current_user.role.value not in ["HR", "SUPER_ADMIN", "ORG_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    schedule = WorkSchedule(
        organization_id=current_user.organization_id,
        department_id=schedule_data.department_id,
        employee_id=schedule_data.employee_id,
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
    
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    
    return schedule


@router.get("/schedules", response_model=List[WorkScheduleResponse])
async def get_work_schedules(
    department_id: Optional[int] = Query(None, description="Filter by department"),
    employee_id: Optional[int] = Query(None, description="Filter by employee"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get work schedules"""
    query = db.query(WorkSchedule).filter(
        WorkSchedule.organization_id == current_user.organization_id
    )
    
    if department_id:
        query = query.filter(WorkSchedule.department_id == department_id)
    
    if employee_id:
        query = query.filter(WorkSchedule.employee_id == employee_id)
    
    schedules = query.filter(WorkSchedule.is_active == True).all()
    return schedules


# Time Off Request endpoints
@router.post("/time-off", response_model=TimeOffRequestResponse)
async def create_time_off_request(
    request_data: TimeOffRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a time off request"""
    # Get employee record
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee record not found"
        )
    
    # Calculate duration
    duration = request_data.end_date - request_data.start_date
    total_days = duration.days + 1
    
    request = TimeOffRequest(
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
        requested_by=current_user.id
    )
    
    db.add(request)
    db.commit()
    db.refresh(request)
    
    return request


@router.get("/time-off", response_model=List[TimeOffRequestResponse])
async def get_time_off_requests(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get time off requests"""
    # Get employee record
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee record not found"
        )
    
    query = db.query(TimeOffRequest).filter(
        TimeOffRequest.employee_id == employee.id
    )
    
    if status:
        query = query.filter(TimeOffRequest.status == status)
    
    requests = query.order_by(TimeOffRequest.created_at.desc()).all()
    return requests 