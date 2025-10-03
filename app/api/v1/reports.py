from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List
from datetime import datetime, date, timedelta
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.employee import Employee
from app.models.organization import Organization
from app.models.attendance import Attendance
from app.models.leave import LeaveRequest
from app.models.payroll import PayrollRecord
from app.api.v1.auth import get_current_user

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard data with organization-specific filtering
    """
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.PAYROLL, UserRole.DIRECTOR, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view dashboard data"
        )
    
    # Set organization filter
    if current_user.role == UserRole.SUPER_ADMIN:
        org_filter = True  # Super admin can see all data
    else:
        org_filter = Employee.organization_id == current_user.organization_id
    
    try:
        # Get employee count
        employee_count = db.query(Employee).filter(org_filter).count()
        
        # Get active employees
        active_employees = db.query(Employee).filter(
            and_(org_filter, Employee.status == "ACTIVE")
        ).count()
        
        # Get recent hires (last 30 days)
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        recent_hires = db.query(Employee).filter(
            and_(
                org_filter,
                Employee.hire_date >= thirty_days_ago
            )
        ).count()
        
        # Get pending leave requests
        pending_leave = db.query(LeaveRequest).join(Employee, LeaveRequest.employee_id == Employee.id).filter(
            and_(
                org_filter,
                LeaveRequest.status == "PENDING"
            )
        ).count()
        
        # Get employee growth data (last 12 months)
        from app.models.department import Department
        employee_growth = []
        for i in range(12):
            month_date = datetime.now().date().replace(day=1)
            if month_date.month - i <= 0:
                month_date = month_date.replace(year=month_date.year - 1, month=12 + (month_date.month - i))
            else:
                month_date = month_date.replace(month=month_date.month - i)
            
            # Count employees hired before or during this month
            month_count = db.query(Employee).filter(
                and_(
                    org_filter,
                    Employee.hire_date <= month_date
                )
            ).count()
            
            month_name = month_date.strftime('%b')
            employee_growth.append({
                "month": month_name,
                "employees": month_count
            })
        
        # Reverse to show oldest to newest
        employee_growth.reverse()
        
        # Get department distribution
        department_distribution = []
        dept_counts = db.query(
            Department.name,
            func.count(Employee.id).label('count')
        ).join(Employee, Department.id == Employee.department_id).filter(
            org_filter
        ).group_by(Department.name).all()
        
        total_employees_for_percentage = max(employee_count, 1)  # Avoid division by zero
        
        for dept_name, count in dept_counts:
            percentage = round((count / total_employees_for_percentage) * 100, 1)
            department_distribution.append({
                "department": dept_name,
                "count": count,
                "percentage": percentage
            })
        
        return {
            "total_employees": employee_count,
            "active_employees": active_employees,
            "recent_hires": recent_hires,
            "pending_leave_requests": pending_leave,
            "employee_growth": employee_growth,
            "department_distribution": department_distribution,
            "organization_id": current_user.organization_id if current_user.role != UserRole.SUPER_ADMIN else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard data: {str(e)}"
        )


@router.get("/employee")
async def get_employee_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """
    Get employee reports with organization-specific filtering
    """
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.PAYROLL, UserRole.DIRECTOR, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view employee reports"
        )
    
    # Set organization filter
    if current_user.role == UserRole.SUPER_ADMIN:
        org_filter = True  # Super admin can see all data
    else:
        org_filter = Employee.organization_id == current_user.organization_id
    
    try:
        # Get employees by status
        employees_by_status = db.query(
            Employee.status,
            func.count(Employee.id).label('count')
        ).filter(org_filter).group_by(Employee.status).all()
        
        # Get employees by employment type
        employees_by_type = db.query(
            Employee.employment_type,
            func.count(Employee.id).label('count')
        ).filter(org_filter).group_by(Employee.employment_type).all()
        
        # Get employees by department (if applicable)
        employees_by_department = db.query(
            Employee.department_id,
            func.count(Employee.id).label('count')
        ).filter(org_filter).group_by(Employee.department_id).all()
        
        return {
            "employees_by_status": [{"status": item.status, "count": item.count} for item in employees_by_status],
            "employees_by_type": [{"type": item.employment_type, "count": item.count} for item in employees_by_type],
            "employees_by_department": [{"department_id": item.department_id, "count": item.count} for item in employees_by_department],
            "organization_id": current_user.organization_id if current_user.role != UserRole.SUPER_ADMIN else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching employee reports: {str(e)}"
        )


@router.get("/attendance")
async def get_attendance_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """
    Get attendance reports with organization-specific filtering
    """
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.PAYROLL, UserRole.DIRECTOR, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view attendance reports"
        )
    
    # Set organization filter
    if current_user.role == UserRole.SUPER_ADMIN:
        org_filter = True  # Super admin can see all data
    else:
        org_filter = Employee.organization_id == current_user.organization_id
    
    try:
        # Set default date range if not provided
        if not start_date:
            start_date = datetime.now().date() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now().date()
        
        # Get attendance records
        attendance_records = db.query(Attendance).join(Employee).filter(
            and_(
                org_filter,
                Attendance.date >= start_date,
                Attendance.date <= end_date
            )
        ).all()
        
        # Calculate attendance statistics
        total_records = len(attendance_records)
        on_time_count = sum(1 for record in attendance_records if record.status == "PRESENT")
        late_count = sum(1 for record in attendance_records if record.status == "LATE")
        absent_count = sum(1 for record in attendance_records if record.status == "ABSENT")
        
        return {
            "total_records": total_records,
            "on_time": on_time_count,
            "late": late_count,
            "absent": absent_count,
            "attendance_rate": (on_time_count + late_count) / total_records * 100 if total_records > 0 else 0,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "organization_id": current_user.organization_id if current_user.role != UserRole.SUPER_ADMIN else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching attendance reports: {str(e)}"
        )


@router.get("/payroll")
async def get_payroll_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None)
):
    """
    Get payroll reports with organization-specific filtering
    """
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.PAYROLL, UserRole.DIRECTOR, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view payroll reports"
        )
    
    # Set organization filter
    if current_user.role == UserRole.SUPER_ADMIN:
        org_filter = True  # Super admin can see all data
    else:
        org_filter = Employee.organization_id == current_user.organization_id
    
    try:
        # Set default month/year if not provided
        if not month or not year:
            current_date = datetime.now()
            month = month or current_date.month
            year = year or current_date.year
        
        # Get payroll records for the specified month
        payroll_records = db.query(PayrollRecord).join(Employee).filter(
            and_(
                org_filter,
                func.extract('month', PayrollRecord.created_at) == month,
                func.extract('year', PayrollRecord.created_at) == year
            )
        ).all()
        
        if not payroll_records:
            return {
                "message": f"No payroll records found for {month}/{year}",
                "total_records": 0,
                "total_amount": 0,
                "organization_id": current_user.organization_id if current_user.role != UserRole.SUPER_ADMIN else None
            }
        
        # Calculate payroll statistics
        total_records = len(payroll_records)
        total_amount = sum(record.gross_pay for record in payroll_records if record.gross_pay)
        
        return {
            "total_records": total_records,
            "total_amount": total_amount,
            "average_pay": total_amount / total_records if total_records > 0 else 0,
            "month": month,
            "year": year,
            "organization_id": current_user.organization_id if current_user.role != UserRole.SUPER_ADMIN else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching payroll reports: {str(e)}"
        ) 