from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.v1.auth import get_current_user
from app.core.mongo import get_mongo_db
from app.models.enums import AttendanceStatus, EmployeeStatus, LeaveStatus, UserRole
from app.models.mongo_models import (
    AttendanceDocument,
    DepartmentDocument,
    EmployeeDocument,
    LeaveRequestDocument,
    PayrollRecordDocument,
    UserDocument,
)

router = APIRouter()


def _require_reporting_role(user: UserDocument) -> None:
    if user.role not in [
        UserRole.SUPER_ADMIN,
        UserRole.ORG_ADMIN,
        UserRole.HR,
        UserRole.PAYROLL,
        UserRole.DIRECTOR,
        UserRole.MANAGER,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access HR reports",
        )


def _org_match(current_user: UserDocument) -> Dict[str, Any]:
    if current_user.role == UserRole.SUPER_ADMIN or not current_user.organization_id:
        return {}
    return {"organization_id": current_user.organization_id}


async def _department_name_map(department_ids: List[PydanticObjectId]) -> Dict[PydanticObjectId, str]:
    if not department_ids:
        return {}
    departments = await DepartmentDocument.find({"_id": {"$in": department_ids}}).to_list()
    return {dept.id: dept.name for dept in departments}


@router.get("/dashboard")
async def get_dashboard_data(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Return key dashboard metrics scoped to the user's organization."""
    if current_user.role not in [
        UserRole.SUPER_ADMIN,
        UserRole.ORG_ADMIN,
        UserRole.HR,
        UserRole.PAYROLL,
        UserRole.DIRECTOR,
        UserRole.MANAGER,
        UserRole.EMPLOYEE,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view dashboard data",
        )

    match_query = _org_match(current_user)

    try:
        employee_count = await EmployeeDocument.find(match_query).count()
        active_employees = await EmployeeDocument.find(
            {**match_query, "status": EmployeeStatus.ACTIVE}
        ).count()

        thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)
        recent_hires = await EmployeeDocument.find(
            {
                **match_query,
                "hire_date": {"$gte": thirty_days_ago},
            }
        ).count()

        pending_leave = await LeaveRequestDocument.find(
            {
                **match_query,
                "status": LeaveStatus.PENDING,
            }
        ).count()

        employee_growth: List[Dict[str, Any]] = []
        base_month = datetime.utcnow().date().replace(day=1)
        for offset in range(11, -1, -1):
            month_start = (base_month - timedelta(days=offset * 30)).replace(day=1)
            month_name = month_start.strftime("%b")
            month_count = await EmployeeDocument.find(
                {
                    **match_query,
                    "hire_date": {"$lte": month_start},
                }
            ).count()
            employee_growth.append({"month": month_name, "employees": month_count})

        pipeline = [
            {"$match": match_query},
            {"$group": {"_id": "$department_id", "count": {"$sum": 1}}},
        ]
        department_counts: Dict[PydanticObjectId, int] = {}
        collection_name = EmployeeDocument.Settings.name
        async for doc in db[collection_name].aggregate(pipeline):
            dept_id = doc["_id"]
            if dept_id:
                department_counts[dept_id] = doc["count"]

        department_map = await _department_name_map(list(department_counts.keys()))
        total_for_percentage = max(employee_count, 1)
        department_distribution = [
            {
                "department": department_map.get(dept_id, "Unknown"),
                "count": count,
                "percentage": round((count / total_for_percentage) * 100, 1),
            }
            for dept_id, count in department_counts.items()
        ]

        # Calculate additional metrics for frontend
        # Attendance rate (last 30 days)
        attendance_window_start = datetime.utcnow().date() - timedelta(days=30)
        attendance_records = await AttendanceDocument.find(
            {
                **match_query,
                "date": {"$gte": attendance_window_start},
            }
        ).to_list()
        total_attendance_records = len(attendance_records)
        present_count = sum(1 for rec in attendance_records if rec.status in [AttendanceStatus.PRESENT, AttendanceStatus.LATE])
        attendance_rate = (present_count / total_attendance_records * 100) if total_attendance_records > 0 else 0

        # Payroll totals (current month)
        now = datetime.utcnow()
        payroll_start = datetime(now.year, now.month, 1)
        if now.month == 12:
            payroll_end = datetime(now.year + 1, 1, 1)
        else:
            payroll_end = datetime(now.year, now.month + 1, 1)
        payroll_match: Dict[str, Any] = {"created_at": {"$gte": payroll_start, "$lt": payroll_end}}
        if match_query.get("organization_id"):
            payroll_match["organization_id"] = match_query["organization_id"]
        payroll_records = await PayrollRecordDocument.find(payroll_match).to_list()
        total_payroll = sum(float(record.gross_pay or 0) for record in payroll_records)
        average_salary = total_payroll / len(payroll_records) if payroll_records else 0

        # Calculate turnover rate (employees who left in last 30 days / total employees)
        terminated_employees = await EmployeeDocument.find(
            {
                **match_query,
                "status": EmployeeStatus.TERMINATED,
                "termination_date": {"$gte": thirty_days_ago},
            }
        ).count()
        turnover_rate = (terminated_employees / employee_count * 100) if employee_count > 0 else 0

        return {
            # Keep original field names for backward compatibility
            "total_employees": employee_count,
            "active_employees": active_employees,
            "recent_hires": recent_hires,
            "pending_leave_requests": pending_leave,
            "employee_growth": employee_growth,
            "department_distribution": department_distribution,
            # Add fields expected by frontend
            "employee_count": employee_count,  # Alias for frontend
            "new_hires": recent_hires,  # Alias for frontend
            "attendance_rate": round(attendance_rate, 1),
            "total_payroll": round(total_payroll, 2),
            "average_salary": round(average_salary, 2),
            "turnover_rate": round(turnover_rate, 1),
            "organization_id": str(current_user.organization_id) if current_user.organization_id else None,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard data: {exc}",
        ) from exc


@router.get("/employee")
async def get_employee_reports(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Return employee distributions by status, employment type, and department."""
    _require_reporting_role(current_user)
    match_query = _org_match(current_user)

    try:
        status_pipeline = [
            {"$match": match_query},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        employees_by_status: List[Dict[str, Any]] = []
        collection_name = EmployeeDocument.Settings.name
        async for doc in db[collection_name].aggregate(status_pipeline):
            employees_by_status.append({"status": doc["_id"], "count": doc["count"]})

        type_pipeline = [
            {"$match": match_query},
            {"$group": {"_id": "$employment_type", "count": {"$sum": 1}}},
        ]
        employees_by_type: List[Dict[str, Any]] = []
        async for doc in db[collection_name].aggregate(type_pipeline):
            employees_by_type.append({"type": doc["_id"], "count": doc["count"]})

        dept_pipeline = [
            {"$match": match_query},
            {"$group": {"_id": "$department_id", "count": {"$sum": 1}}},
        ]
        employees_by_department: List[Dict[str, Any]] = []
        async for doc in db[collection_name].aggregate(dept_pipeline):
            employees_by_department.append({"department_id": str(doc["_id"]), "count": doc["count"]})

        return {
            "employees_by_status": employees_by_status,
            "employees_by_type": employees_by_type,
            "employees_by_department": employees_by_department,
            "organization_id": str(current_user.organization_id) if current_user.organization_id else None,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching employee reports: {exc}",
        ) from exc


@router.get("/attendance")
async def get_attendance_reports(
    current_user: UserDocument = Depends(get_current_user),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Return attendance stats for the selected date range."""
    _require_reporting_role(current_user)

    match_query = _org_match(current_user)
    start = start_date or (datetime.utcnow().date() - timedelta(days=30))
    end = end_date or datetime.utcnow().date()
    match_query["date"] = {"$gte": start, "$lte": end}

    try:
        records = await AttendanceDocument.find(match_query).to_list()
        total_records = len(records)
        on_time = sum(1 for rec in records if rec.status == AttendanceStatus.PRESENT)
        late = sum(1 for rec in records if rec.status == AttendanceStatus.LATE)
        absent = sum(1 for rec in records if rec.status == AttendanceStatus.ABSENT)

        return {
            "total_records": total_records,
            "on_time": on_time,
            "late": late,
            "absent": absent,
            "attendance_rate": ((on_time + late) / total_records * 100) if total_records else 0,
            "date_range": {"start_date": start.isoformat(), "end_date": end.isoformat()},
            "organization_id": str(current_user.organization_id) if current_user.organization_id else None,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching attendance reports: {exc}",
        ) from exc


@router.get("/payroll")
async def get_payroll_reports(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000),
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Return payroll totals for the selected month."""
    _require_reporting_role(current_user)

    now = datetime.utcnow()
    target_month = month or now.month
    target_year = year or now.year

    start = datetime(target_year, target_month, 1)
    if target_month == 12:
        end = datetime(target_year + 1, 1, 1)
    else:
        end = datetime(target_year, target_month + 1, 1)

    match_query: Dict[str, Any] = {"created_at": {"$gte": start, "$lt": end}}
    if current_user.role != UserRole.SUPER_ADMIN and current_user.organization_id:
        match_query["organization_id"] = current_user.organization_id

    try:
        records = await PayrollRecordDocument.find(match_query).to_list()
        total_records = len(records)
        total_amount = sum(float(record.gross_pay or 0) for record in records)

        if not records:
            return {
                "message": f"No payroll records found for {target_month}/{target_year}",
                "total_records": 0,
                "total_amount": 0,
                "organization_id": str(current_user.organization_id) if current_user.organization_id else None,
            }

        return {
            "total_records": total_records,
            "total_amount": total_amount,
            "average_pay": total_amount / total_records if total_records else 0,
            "month": target_month,
            "year": target_year,
            "organization_id": str(current_user.organization_id) if current_user.organization_id else None,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching payroll reports: {exc}",
        ) from exc


@router.get("/summary")
async def get_reports_summary(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Provide a lightweight collection of key metrics for the reports overview page.
    Designed to be resilient even when certain collections are empty.
    """
    _require_reporting_role(current_user)
    match_query = _org_match(current_user)

    try:
        total_employees = await EmployeeDocument.find(match_query).count()
        active_employees = await EmployeeDocument.find(
            {**match_query, "status": EmployeeStatus.ACTIVE}
        ).count()
        pending_employees = await EmployeeDocument.find(
            {**match_query, "status": {"$ne": EmployeeStatus.ACTIVE}}
        ).count()

        department_query = {}
        if match_query.get("organization_id"):
            department_query["organization_id"] = match_query["organization_id"]
        total_departments = await DepartmentDocument.find(department_query).count()

        pending_leave = await LeaveRequestDocument.find(
            {**match_query, "status": LeaveStatus.PENDING}
        ).count()

        attendance_window_start = datetime.utcnow().date() - timedelta(days=30)
        attendance_records = await AttendanceDocument.find(
            {
                **match_query,
                "date": {"$gte": attendance_window_start},
            }
        ).to_list()
        on_time = sum(1 for rec in attendance_records if rec.status == AttendanceStatus.PRESENT)
        late = sum(1 for rec in attendance_records if rec.status == AttendanceStatus.LATE)
        absent = sum(1 for rec in attendance_records if rec.status == AttendanceStatus.ABSENT)

        now = datetime.utcnow()
        payroll_start = datetime(now.year, now.month, 1)
        if now.month == 12:
            payroll_end = datetime(now.year + 1, 1, 1)
        else:
            payroll_end = datetime(now.year, now.month + 1, 1)
        payroll_match: Dict[str, Any] = {"created_at": {"$gte": payroll_start, "$lt": payroll_end}}
        if match_query.get("organization_id"):
            payroll_match["organization_id"] = match_query["organization_id"]
        payroll_records = await PayrollRecordDocument.find(payroll_match).to_list()
        payroll_total = sum(float(record.gross_pay or 0) for record in payroll_records)

        return {
            "employees": {
                "total": total_employees,
                "active": active_employees,
                "pending_or_inactive": pending_employees,
            },
            "departments": {
                "total": total_departments,
            },
            "leave": {
                "pending_requests": pending_leave,
            },
            "attendance_last_30_days": {
                "records": len(attendance_records),
                "on_time": on_time,
                "late": late,
                "absent": absent,
            },
            "payroll_current_month": {
                "records": len(payroll_records),
                "total_paid": payroll_total,
            },
            "organization_id": str(current_user.organization_id) if current_user.organization_id else None,
            "last_updated": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error building reports summary: {exc}",
        ) from exc