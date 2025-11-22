import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from beanie import PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.v1.auth import get_current_user
from app.core.mongo import get_mongo_db
from app.models.enums import (
    DepartmentStatus,
    EmployeeStatus,
    PayrollStatus,
    SalaryComponentType,
    UserRole,
)
from app.models.mongo_models import (
    DepartmentDocument,
    EmployeeDocument,
    OrganizationDocument,
    PayrollComponentDocument,
    PayrollPeriodDocument,
    PayrollRecordDocument,
    PayrollSettingsDocument,
    UserDocument,
)
from app.schemas.payroll import (
    PayrollRecordCreate,
    PayrollRecordUpdate,
    PayrollSettingsResponse,
    PayrollSettingsUpdate,
)
from app.utils.pdf_generator import generate_payroll_pdf

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWANCE_COMPONENT_TYPES = {
    SalaryComponentType.ALLOWANCE,
    SalaryComponentType.BONUS,
    SalaryComponentType.OVERTIME,
    SalaryComponentType.COMMISSION,
    SalaryComponentType.HOUSING_ALLOWANCE,
    SalaryComponentType.TRANSPORT_ALLOWANCE,
    SalaryComponentType.MEDICAL_ALLOWANCE,
    SalaryComponentType.MEAL_ALLOWANCE,
}

DEDUCTION_COMPONENT_TYPES = {
    SalaryComponentType.DEDUCTION,
    SalaryComponentType.TAX,
    SalaryComponentType.INSURANCE,
    SalaryComponentType.PENSION,
    SalaryComponentType.LOAN_DEDUCTION,
    SalaryComponentType.ADVANCE_DEDUCTION,
    SalaryComponentType.UNIFORM_DEDUCTION,
    SalaryComponentType.PARKING_DEDUCTION,
    SalaryComponentType.LATE_PENALTY,
}

FIELD_COMPONENT_MAP = {
    "housing_allowance": SalaryComponentType.HOUSING_ALLOWANCE,
    "transport_allowance": SalaryComponentType.TRANSPORT_ALLOWANCE,
    "medical_allowance": SalaryComponentType.MEDICAL_ALLOWANCE,
    "meal_allowance": SalaryComponentType.MEAL_ALLOWANCE,
    "loan_deduction": SalaryComponentType.LOAN_DEDUCTION,
    "advance_deduction": SalaryComponentType.ADVANCE_DEDUCTION,
    "uniform_deduction": SalaryComponentType.UNIFORM_DEDUCTION,
    "parking_deduction": SalaryComponentType.PARKING_DEDUCTION,
    "late_penalty": SalaryComponentType.LATE_PENALTY,
}

ALLOWANCE_FIELDS = [
    "housing_allowance",
    "transport_allowance",
    "medical_allowance",
    "meal_allowance",
]

DEDUCTION_FIELDS = [
    "loan_deduction",
    "advance_deduction",
    "uniform_deduction",
    "parking_deduction",
    "late_penalty",
]


def _parse_object_id(value: str, field_name: str) -> PydanticObjectId:
    try:
        return PydanticObjectId(value)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}",
        )


def _employee_display(employee: Optional[EmployeeDocument]) -> str:
    if not employee:
        return "Unknown Employee"
    name = f"{employee.first_name or ''} {employee.last_name or ''}".strip()
    return name or employee.employee_id


def _department_name_for_employee(
    employee: Optional[EmployeeDocument],
    department_map: Optional[Dict[PydanticObjectId, DepartmentDocument]],
) -> str:
    if not employee or not employee.department_id:
        return "No Department"
    if department_map and employee.department_id in department_map:
        return department_map[employee.department_id].name
    return "No Department"


def _calculate_component_totals(
    components: List[PayrollComponentDocument],
) -> Dict[str, float]:
    totals: Dict[str, float] = {"allowances": 0.0, "deductions": 0.0}
    totals.update({field: 0.0 for field in FIELD_COMPONENT_MAP})

    for component in components:
        amount = float(component.amount or Decimal("0"))
        if component.component_type in ALLOWANCE_COMPONENT_TYPES:
            totals["allowances"] += amount
        if component.component_type in DEDUCTION_COMPONENT_TYPES:
            totals["deductions"] += abs(amount)
        for field, comp_type in FIELD_COMPONENT_MAP.items():
            if component.component_type == comp_type:
                field_amount = abs(amount) if comp_type in DEDUCTION_COMPONENT_TYPES else amount
                totals[field] = field_amount

    totals["allowances"] = round(totals["allowances"], 2)
    totals["deductions"] = round(totals["deductions"], 2)
    for field in FIELD_COMPONENT_MAP:
        totals[field] = round(totals[field], 2)
    return totals


async def _get_components_map(
    record_ids: List[PydanticObjectId],
) -> Dict[PydanticObjectId, List[PayrollComponentDocument]]:
    if not record_ids:
        return {}
    components = await PayrollComponentDocument.find(
        {"payroll_record_id": {"$in": record_ids}}
    ).to_list()
    comp_map: Dict[PydanticObjectId, List[PayrollComponentDocument]] = {}
    for component in components:
        comp_map.setdefault(component.payroll_record_id, []).append(component)
    return comp_map


async def _get_employee_and_department_maps(
    records: List[PayrollRecordDocument],
) -> Tuple[
    Dict[PydanticObjectId, EmployeeDocument],
    Dict[PydanticObjectId, DepartmentDocument],
]:
    employee_ids = {record.employee_id for record in records if record.employee_id}
    if not employee_ids:
        return {}, {}

    employees = await EmployeeDocument.find({"_id": {"$in": list(employee_ids)}}).to_list()
    employee_map = {employee.id: employee for employee in employees}

    department_ids = {employee.department_id for employee in employees if employee.department_id}
    department_map: Dict[PydanticObjectId, DepartmentDocument] = {}
    if department_ids:
        departments = await DepartmentDocument.find({"_id": {"$in": list(department_ids)}}).to_list()
        department_map = {department.id: department for department in departments}

    return employee_map, department_map


async def _serialize_payroll_record(
    record: PayrollRecordDocument,
    employee_map: Optional[Dict[PydanticObjectId, EmployeeDocument]] = None,
    department_map: Optional[Dict[PydanticObjectId, DepartmentDocument]] = None,
    component_map: Optional[Dict[PydanticObjectId, List[PayrollComponentDocument]]] = None,
) -> Dict[str, Any]:
    employee = None
    if employee_map is not None:
        employee = employee_map.get(record.employee_id)
    else:
        employee = await EmployeeDocument.get(record.employee_id)

    department_name = _department_name_for_employee(employee, department_map)

    if component_map is not None and record.id in component_map:
        components = component_map[record.id]
    else:
        components = await PayrollComponentDocument.find(
            {"payroll_record_id": record.id}
        ).to_list()

    component_totals = _calculate_component_totals(components)

    return {
        "id": str(record.id),
        "employee": _employee_display(employee),
        "employee_id": employee.employee_id if employee else None,
        "department": department_name,
        "basic_salary": float(record.basic_salary or Decimal("0")),
        "allowances": component_totals["allowances"],
        "deductions": component_totals["deductions"],
        "net_salary": float(record.net_pay or Decimal("0")),
        "status": record.status.value if isinstance(record.status, PayrollStatus) else record.status,
        "pay_date": record.created_at.date().isoformat() if record.created_at else None,
        "housing_allowance": component_totals["housing_allowance"],
        "transport_allowance": component_totals["transport_allowance"],
        "medical_allowance": component_totals["medical_allowance"],
        "meal_allowance": component_totals["meal_allowance"],
        "loan_deduction": component_totals["loan_deduction"],
        "advance_deduction": component_totals["advance_deduction"],
        "uniform_deduction": component_totals["uniform_deduction"],
        "parking_deduction": component_totals["parking_deduction"],
        "late_penalty": component_totals["late_penalty"],
    }


async def _resolve_optional_org_id(
    current_user: UserDocument,
    organization_id: Optional[str],
) -> Optional[PydanticObjectId]:
    if organization_id:
        org_id = _parse_object_id(organization_id, "organization_id")
        organization = await OrganizationDocument.get(org_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        if current_user.role != UserRole.SUPER_ADMIN and current_user.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to organization",
            )
        return org_id

    if current_user.role == UserRole.SUPER_ADMIN:
        return current_user.organization_id

    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required",
        )

    return current_user.organization_id


async def _require_org_id(
    current_user: UserDocument,
    organization_id: Optional[str] = None,
) -> PydanticObjectId:
    resolved = await _resolve_optional_org_id(current_user, organization_id)
    if not resolved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required",
        )
    return resolved


async def _get_employee_by_identifier(identifier: Any) -> EmployeeDocument:
    if identifier in (None, "", 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID is required",
        )

    identifier_str = str(identifier)
    employee = None
    try:
        employee_id = PydanticObjectId(identifier_str)
    except Exception:
        employee_id = None

    if employee_id:
        employee = await EmployeeDocument.get(employee_id)

    if not employee:
        employee = await EmployeeDocument.find_one(
            EmployeeDocument.employee_id == identifier_str
        )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    return employee


def _period_dates(month: int, year: int) -> Tuple[date, date]:
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    return start_date, end_date


def _month_datetime_bounds(month: int, year: int) -> Tuple[datetime, datetime]:
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    return start, end


async def _get_or_create_period(
    organization_id: PydanticObjectId,
    month: int,
    year: int,
) -> PayrollPeriodDocument:
    start_date, end_date = _period_dates(month, year)
    period = await PayrollPeriodDocument.find_one(
        {
            "organization_id": organization_id,
            "start_date": start_date,
        }
    )
    if period:
        return period

    period = PayrollPeriodDocument(
        organization_id=organization_id,
        name=f"Payroll Period {month}/{year}",
        period_type="MONTHLY",
        start_date=start_date,
        end_date=end_date,
        pay_date=end_date,
        processing_date=date.today(),
        status=PayrollStatus.PROCESSING,
    )
    await period.insert()
    return period


async def _apply_component_updates(
    record_id: PydanticObjectId,
    updates: Dict[str, Optional[float]],
    employee_name: str,
) -> None:
    for field, component_type in FIELD_COMPONENT_MAP.items():
        if field not in updates:
            continue
        value = updates[field]
        if value is None:
            continue
        if value < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field.replace('_', ' ').title()} cannot be negative",
            )

        existing = await PayrollComponentDocument.find(
            {
                "payroll_record_id": record_id,
                "component_type": component_type,
            }
        ).to_list()
        for component in existing:
            await component.delete()

        if value == 0:
            continue

        amount = Decimal(str(value))
        if component_type in DEDUCTION_COMPONENT_TYPES:
            amount = -amount

        component = PayrollComponentDocument(
            payroll_record_id=record_id,
            name=field.replace("_", " ").title(),
            component_type=component_type,
            amount=amount,
            is_taxable=component_type in ALLOWANCE_COMPONENT_TYPES,
            description=f"{field.replace('_', ' ').title()} for {employee_name}",
        )
        await component.insert()


async def _refresh_record_totals(record: PayrollRecordDocument) -> None:
    components = await PayrollComponentDocument.find(
        {"payroll_record_id": record.id}
    ).to_list()
    totals = _calculate_component_totals(components)

    record.total_allowances = Decimal(str(totals["allowances"]))
    record.total_deductions = Decimal(str(totals["deductions"]))
    base_salary = record.basic_salary or Decimal("0")
    record.gross_pay = base_salary + record.total_allowances
    record.net_pay = record.gross_pay - record.total_deductions
    await record.save()


def _settings_to_response(settings: PayrollSettingsDocument) -> PayrollSettingsResponse:
    return PayrollSettingsResponse(
        id=str(settings.id),
        organization_id=str(settings.organization_id),
        payroll_cycle=settings.payroll_cycle,
        pay_day=settings.pay_day,
        currency=settings.currency,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )

async def _get_records_for_period(
    current_user: UserDocument,
    month: int,
    year: int,
    organization_id: Optional[str],
) -> Tuple[
    List[PayrollRecordDocument],
    Dict[PydanticObjectId, EmployeeDocument],
    Dict[PydanticObjectId, DepartmentDocument],
]:
    start_dt, end_dt = _month_datetime_bounds(month, year)
    org_filter = await _resolve_optional_org_id(current_user, organization_id)

    query: Dict[str, Any] = {
        "created_at": {
            "$gte": start_dt,
            "$lt": end_dt,
        }
    }
    if org_filter:
        query["organization_id"] = org_filter

    records = await PayrollRecordDocument.find(query).to_list()
    employee_map, department_map = await _get_employee_and_department_maps(records)
    return records, employee_map, department_map


async def recalculate_payroll_period_totals(payroll_period_id: PydanticObjectId) -> None:
    """Recalculate and update payroll period totals."""
    records = await PayrollRecordDocument.find(
        PayrollRecordDocument.payroll_period_id == payroll_period_id
    ).to_list()

    total_gross = sum((record.gross_pay or Decimal("0")) for record in records)
    total_net = sum((record.net_pay or Decimal("0")) for record in records)
    total_deductions = total_gross - total_net

    payroll_period = await PayrollPeriodDocument.get(payroll_period_id)
    if not payroll_period:
        logger.warning("Payroll period %s not found for recalculation", payroll_period_id)
        return

    payroll_period.total_gross_pay = total_gross
    payroll_period.total_net_pay = total_net
    payroll_period.total_deductions = total_deductions
    payroll_period.updated_at = datetime.utcnow()
    await payroll_period.save()

@router.post("/process")
async def process_payroll(
    organization_id: Optional[str] = Query(
        None,
        description="Optional organization scope for super administrators",
    ),
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Process payroll for all active employees in the current month."""
    if current_user.role not in [UserRole.HR, UserRole.PAYROLL, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to process payroll",
        )

    target_org_id = await _require_org_id(current_user, organization_id)

    employees = await EmployeeDocument.find(
        {
            "organization_id": target_org_id,
            "status": EmployeeStatus.ACTIVE,
        }
    ).to_list()
    if not employees:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active employees found",
        )

    now = datetime.utcnow()
    current_month = now.month
    current_year = now.year
    start_date, _ = _period_dates(current_month, current_year)

    existing_period = await PayrollPeriodDocument.find_one(
        {
            "organization_id": target_org_id,
            "start_date": start_date,
        }
    )
    if existing_period:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payroll for {current_month}/{current_year} already processed",
        )

    payroll_period = await _get_or_create_period(target_org_id, current_month, current_year)

    processed_count = 0
    total_gross = Decimal("0")
    total_net = Decimal("0")

    for employee in employees:
        base_salary = Decimal(str(employee.base_salary or 50000))
        monthly_salary = base_salary / Decimal("12")

        allowances = monthly_salary * Decimal("0.10")
        housing_allowance = monthly_salary * Decimal("0.05")
        transport_allowance = Decimal("2000")
        medical_allowance = Decimal("1500")
        meal_allowance = Decimal("1000")

        deductions = monthly_salary * Decimal("0.20")
        loan_deduction = Decimal("5000")
        advance_deduction = Decimal("2000")
        uniform_deduction = Decimal("500")
        parking_deduction = Decimal("300")
        late_penalty = Decimal("0")

        total_allocations = (
            allowances
            + housing_allowance
            + transport_allowance
            + medical_allowance
            + meal_allowance
        )
        total_additional_deductions = (
            loan_deduction
            + advance_deduction
            + uniform_deduction
            + parking_deduction
            + late_penalty
        )

        gross_pay = monthly_salary + total_allocations
        net_pay = gross_pay - deductions - total_additional_deductions

        payroll_record = PayrollRecordDocument(
            payroll_period_id=payroll_period.id,
            employee_id=employee.id,
            organization_id=target_org_id,
            base_salary=monthly_salary,
            basic_salary=monthly_salary,
            total_earnings=monthly_salary,
            total_allowances=total_allocations,
            total_bonuses=Decimal("0"),
            total_overtime=Decimal("0"),
            total_commission=Decimal("0"),
            total_deductions=deductions + total_additional_deductions,
            total_taxes=deductions * Decimal("0.8"),
            total_insurance=deductions * Decimal("0.1"),
            total_pension=deductions * Decimal("0.1"),
            gross_pay=gross_pay,
            net_pay=net_pay,
            regular_hours=160.0,
            overtime_hours=0.0,
            total_hours=160.0,
            status=PayrollStatus.PROCESSING,
            is_approved=False,
            notes=f"Auto-processed payroll for {_employee_display(employee)}",
        )
        await payroll_record.insert()

        component_payloads = [
            ("Basic Salary", SalaryComponentType.BASIC, monthly_salary, True),
            ("Monthly Allowance", SalaryComponentType.ALLOWANCE, allowances, True),
            ("Housing Allowance", SalaryComponentType.HOUSING_ALLOWANCE, housing_allowance, True),
            ("Transport Allowance", SalaryComponentType.TRANSPORT_ALLOWANCE, transport_allowance, True),
            ("Medical Allowance", SalaryComponentType.MEDICAL_ALLOWANCE, medical_allowance, True),
            ("Meal Allowance", SalaryComponentType.MEAL_ALLOWANCE, meal_allowance, True),
            ("Income Tax", SalaryComponentType.TAX, -(deductions * Decimal("0.8")), False),
            ("Health Insurance", SalaryComponentType.INSURANCE, -(deductions * Decimal("0.1")), False),
            ("Pension Contribution", SalaryComponentType.PENSION, -(deductions * Decimal("0.1")), False),
            ("Loan Deduction", SalaryComponentType.LOAN_DEDUCTION, -loan_deduction, False),
            ("Advance Deduction", SalaryComponentType.ADVANCE_DEDUCTION, -advance_deduction, False),
            ("Uniform Deduction", SalaryComponentType.UNIFORM_DEDUCTION, -uniform_deduction, False),
            ("Parking Deduction", SalaryComponentType.PARKING_DEDUCTION, -parking_deduction, False),
            ("Late Penalty", SalaryComponentType.LATE_PENALTY, -late_penalty, False),
        ]

        for name, component_type, amount, is_taxable in component_payloads:
            component = PayrollComponentDocument(
                payroll_record_id=payroll_record.id,
                name=name,
                component_type=component_type,
                amount=amount,
                is_taxable=is_taxable,
                description=f"{name} for {_employee_display(employee)}",
            )
            await component.insert()

        processed_count += 1
        total_gross += gross_pay
        total_net += net_pay

    payroll_period.total_gross_pay = total_gross
    payroll_period.total_net_pay = total_net
    payroll_period.total_deductions = total_gross - total_net
    payroll_period.status = PayrollStatus.PROCESSING
    await payroll_period.save()

    return {
        "message": f"Payroll processed successfully for {processed_count} employees",
        "processed_count": processed_count,
        "total_gross_pay": float(total_gross),
        "total_net_pay": float(total_net),
        "period_id": str(payroll_period.id),
    }

@router.post("/generate-report")
async def generate_payroll_report(
    report_type: str = Query(..., description="summary, detailed, tax, or benefits"),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000),
    organization_id: Optional[str] = Query(None),
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Generate payroll report data."""
    if current_user.role not in [UserRole.HR, UserRole.PAYROLL, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to generate reports",
        )

    now = datetime.utcnow()
    target_month = month or now.month
    target_year = year or now.year

    records, employee_map, department_map = await _get_records_for_period(
        current_user,
        target_month,
        target_year,
        organization_id,
    )

    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No payroll records found for {target_month}/{target_year}",
        )

    report_key = report_type.lower()
    if report_key == "summary":
        return generate_summary_report(records, target_month, target_year, employee_map, department_map)
    if report_key == "detailed":
        return generate_detailed_report(records, target_month, target_year, employee_map, department_map)
    if report_key == "tax":
        return generate_tax_report(records, target_month, target_year)
    if report_key == "benefits":
        return generate_benefits_report(records, target_month, target_year)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid report type. Use summary, detailed, tax, or benefits",
    )


@router.get("/download-pdf")
async def download_payroll_pdf(
    report_type: str = Query(..., description="summary, detailed, tax, or benefits"),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000),
    organization_id: Optional[str] = Query(None),
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Download payroll report as PDF."""
    report_data = await generate_payroll_report(
        report_type=report_type,
        month=month,
        year=year,
        organization_id=organization_id,
        current_user=current_user,
        db=db,
    )

    pdf_buffer = generate_payroll_pdf(report_type, report_data)
    target_month = month or datetime.utcnow().month
    target_year = year or datetime.utcnow().year
    filename = f"payroll_{report_type}_{target_month}_{target_year}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

@router.get("/summary")
async def get_payroll_summary(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Return payroll summary metrics for the current organization context."""
    org_filter = await _resolve_optional_org_id(current_user, None)

    employee_query: Dict[str, Any] = {"status": EmployeeStatus.ACTIVE}
    if org_filter:
        employee_query["organization_id"] = org_filter
    total_employees = await EmployeeDocument.find(employee_query).count()

    now = datetime.utcnow()
    start_dt, end_dt = _month_datetime_bounds(now.month, now.year)

    paid_query: Dict[str, Any] = {
        "status": PayrollStatus.PAID,
        "created_at": {"$gte": start_dt, "$lt": end_dt},
    }
    if org_filter:
        paid_query["organization_id"] = org_filter

    paid_records = await PayrollRecordDocument.find(paid_query).to_list()
    total_payroll = sum(float(record.gross_pay or Decimal("0")) for record in paid_records)
    average_salary = (
        sum(float(record.net_pay or Decimal("0")) for record in paid_records) / len(paid_records)
        if paid_records
        else 0.0
    )

    pending_query: Dict[str, Any] = {"status": PayrollStatus.PROCESSING}
    processed_query: Dict[str, Any] = {"status": PayrollStatus.PAID}
    if org_filter:
        pending_query["organization_id"] = org_filter
        processed_query["organization_id"] = org_filter

    pending_payments = await PayrollRecordDocument.find(pending_query).count()
    processed_payments = await PayrollRecordDocument.find(processed_query).count()

    return {
        "total_employees": total_employees,
        "total_payroll": round(total_payroll, 2),
        "average_salary": round(average_salary, 2),
        "pending_payments": pending_payments,
        "processed_payments": processed_payments,
    }

@router.get("/records")
async def get_payroll_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: Optional[str] = Query(None, alias="status"),
    department: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None),
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """List payroll records with optional filtering."""
    org_filter = await _resolve_optional_org_id(current_user, organization_id)

    query: Dict[str, Any] = {}
    if org_filter:
        query["organization_id"] = org_filter

    if status_filter:
        try:
            query["status"] = PayrollStatus(status_filter.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status filter",
            )

    if department:
        dept_query: Dict[str, Any] = {"name": department, "status": DepartmentStatus.ACTIVE}
        if org_filter:
            dept_query["organization_id"] = org_filter

        departments = await DepartmentDocument.find(dept_query).to_list()
        if not departments:
            return {"records": [], "total": 0, "skip": skip, "limit": limit}

        dept_ids = [dept.id for dept in departments]
        employees_in_dept = await EmployeeDocument.find(
            {"department_id": {"$in": dept_ids}}
        ).to_list()
        employee_ids = [employee.id for employee in employees_in_dept]
        if not employee_ids:
            return {"records": [], "total": 0, "skip": skip, "limit": limit}
        query["employee_id"] = {"$in": employee_ids}

    total = await PayrollRecordDocument.find(query).count()
    records = (
        await PayrollRecordDocument.find(query)
        .sort("-created_at")
        .skip(skip)
        .limit(limit)
        .to_list()
    )

    employee_map, department_map = await _get_employee_and_department_maps(records)
    component_map = await _get_components_map([record.id for record in records])

    serialized = []
    for record in records:
        serialized.append(
            await _serialize_payroll_record(
                record,
                employee_map=employee_map,
                department_map=department_map,
                component_map=component_map,
            )
        )

    return {
        "records": serialized,
        "total": total,
        "skip": skip,
        "limit": limit,
    }

@router.post("/records")
async def create_payroll_record(
    record_data: PayrollRecordCreate,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Create a payroll record for a single employee."""
    if current_user.role not in [UserRole.HR, UserRole.PAYROLL, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create payroll records",
        )

    employee = await _get_employee_by_identifier(record_data.employee_id)
    if current_user.role != UserRole.SUPER_ADMIN and employee.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this employee",
        )

    now = datetime.utcnow()
    period = await _get_or_create_period(employee.organization_id, now.month, now.year)

    basic_salary = Decimal(str(record_data.basic_salary))
    allowance_total = sum(
        Decimal(str(getattr(record_data, field) or 0))
        for field in ALLOWANCE_FIELDS
    )
    deduction_total = sum(
        Decimal(str(getattr(record_data, field) or 0))
        for field in DEDUCTION_FIELDS
    )

    payroll_record = PayrollRecordDocument(
        payroll_period_id=period.id,
        employee_id=employee.id,
        organization_id=employee.organization_id,
        base_salary=basic_salary,
        basic_salary=basic_salary,
        total_earnings=basic_salary,
        total_allowances=allowance_total,
        total_bonuses=Decimal("0"),
        total_overtime=Decimal("0"),
        total_commission=Decimal("0"),
        total_deductions=deduction_total,
        total_taxes=Decimal("0"),
        total_insurance=Decimal("0"),
        total_pension=Decimal("0"),
        gross_pay=basic_salary + allowance_total,
        net_pay=basic_salary + allowance_total - deduction_total,
        regular_hours=160.0,
        overtime_hours=0.0,
        total_hours=160.0,
        status=record_data.status,
        is_approved=False,
        notes=record_data.notes or f"Manual payroll record for {_employee_display(employee)}",
    )
    await payroll_record.insert()

    component_updates = {field: getattr(record_data, field, None) for field in FIELD_COMPONENT_MAP}
    await _apply_component_updates(payroll_record.id, component_updates, _employee_display(employee))
    await _refresh_record_totals(payroll_record)
    await recalculate_payroll_period_totals(payroll_record.payroll_period_id)

    serialized = await _serialize_payroll_record(payroll_record)
    return {
        "message": "Payroll record created successfully",
        "record_id": str(payroll_record.id),
        "created_record": serialized,
    }

@router.put("/records/{record_id}")
async def update_payroll_record(
    record_id: str,
    record_data: PayrollRecordUpdate,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Update an existing payroll record."""
    if current_user.role not in [UserRole.HR, UserRole.PAYROLL, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update payroll records",
        )

    record_obj_id = _parse_object_id(record_id, "record_id")
    record = await PayrollRecordDocument.get(record_obj_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll record not found",
        )

    if current_user.role != UserRole.SUPER_ADMIN and record.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this payroll record",
        )

    update_payload = record_data.dict(exclude_unset=True)

    if "basic_salary" in update_payload and update_payload["basic_salary"] is not None:
        if update_payload["basic_salary"] < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Basic salary cannot be negative",
            )
        record.basic_salary = Decimal(str(update_payload["basic_salary"]))

    if "status" in update_payload and update_payload["status"]:
        record.status = update_payload["status"]

    employee = await EmployeeDocument.get(record.employee_id)
    component_updates = {field: update_payload.get(field) for field in FIELD_COMPONENT_MAP}
    await _apply_component_updates(record.id, component_updates, _employee_display(employee))
    await _refresh_record_totals(record)
    await recalculate_payroll_period_totals(record.payroll_period_id)

    serialized = await _serialize_payroll_record(record)
    return {
        "message": "Payroll record updated successfully",
        "record_id": record_id,
        "updated_record": serialized,
    }

@router.get("/activity")
async def get_payroll_activity(
    limit: int = Query(10, ge=1, le=100),
    organization_id: Optional[str] = Query(None),
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Return recent payroll activity entries."""
    org_filter = await _resolve_optional_org_id(current_user, organization_id)
    query: Dict[str, Any] = {}
    if org_filter:
        query["organization_id"] = org_filter

    records = (
        await PayrollRecordDocument.find(query)
        .sort("-created_at")
        .limit(limit)
        .to_list()
    )

    employee_map, _ = await _get_employee_and_department_maps(records)
    activities = []
    for record in records:
        employee = employee_map.get(record.employee_id)
        activities.append(
            {
                "action": f"Payroll processed for {_employee_display(employee)}",
                "date": record.created_at.date().isoformat() if record.created_at else None,
                "status": record.status.value if isinstance(record.status, PayrollStatus) else record.status,
            }
        )

    return activities


@router.get("/departments")
async def get_departments(
    organization_id: Optional[str] = Query(None),
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """List active departments for payroll filtering."""
    org_filter = await _resolve_optional_org_id(current_user, organization_id)

    query: Dict[str, Any] = {"status": DepartmentStatus.ACTIVE}
    if org_filter:
        query["organization_id"] = org_filter

    departments = await DepartmentDocument.find(query).to_list()
    return sorted({dept.name for dept in departments if dept.name})


@router.get("/payslips")
async def get_payslips(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    return {"message": "Payslips endpoint not yet implemented"}


@router.get("/payslips/{payslip_id}")
async def get_payslip(
    payslip_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    return {"message": f"Payslip {payslip_id} endpoint not yet implemented"}


@router.get("/reports")
async def get_payroll_reports_placeholder():
    return {"message": "Payroll reports endpoint not yet implemented"}

@router.get("/settings", response_model=PayrollSettingsResponse)
async def get_payroll_settings(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    if current_user.role not in [UserRole.HR, UserRole.PAYROLL, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view payroll settings",
        )

    org_id = await _require_org_id(current_user)
    settings = await PayrollSettingsDocument.find_one({"organization_id": org_id})
    if not settings:
        now = datetime.utcnow()
        return PayrollSettingsResponse(
            id=None,
            organization_id=str(org_id),
            payroll_cycle="Monthly",
            pay_day="Last day of month",
            currency="USD ($)",
            created_at=now,
            updated_at=now,
        )
    return _settings_to_response(settings)


@router.put("/settings")
async def update_payroll_settings(
    settings_data: PayrollSettingsUpdate,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    if current_user.role not in [UserRole.HR, UserRole.PAYROLL, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update payroll settings",
        )

    org_id = await _require_org_id(current_user)
    settings = await PayrollSettingsDocument.find_one({"organization_id": org_id})

    if settings:
        update_data = settings_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)
        settings.updated_at = datetime.utcnow()
        await settings.save()
    else:
        settings = PayrollSettingsDocument(
            organization_id=org_id,
            payroll_cycle=settings_data.payroll_cycle or "Monthly",
            pay_day=settings_data.pay_day or "Last day of month",
            currency=settings_data.currency or "USD ($)",
        )
        await settings.insert()

    return {
        "message": "Payroll settings updated successfully",
        "settings": _settings_to_response(settings),
    }

def generate_summary_report(
    payroll_records: List[PayrollRecordDocument],
    month: int,
    year: int,
    employee_map: Dict[PydanticObjectId, EmployeeDocument],
    department_map: Dict[PydanticObjectId, DepartmentDocument],
) -> Dict[str, Any]:
    total_employees = len(payroll_records)
    total_gross = sum(float(record.gross_pay or Decimal("0")) for record in payroll_records)
    total_net = sum(float(record.net_pay or Decimal("0")) for record in payroll_records)
    total_deductions = sum(float(record.total_deductions or Decimal("0")) for record in payroll_records)

    dept_stats: Dict[str, Dict[str, float]] = {}
    for record in payroll_records:
        employee = employee_map.get(record.employee_id)
        dept_name = _department_name_for_employee(employee, department_map)
        stats = dept_stats.setdefault(
            dept_name,
            {"employee_count": 0, "total_gross": 0.0, "total_net": 0.0, "avg_salary": 0.0},
        )
        stats["employee_count"] += 1
        stats["total_gross"] += float(record.gross_pay or Decimal("0"))
        stats["total_net"] += float(record.net_pay or Decimal("0"))

    for stats in dept_stats.values():
        if stats["employee_count"]:
            stats["avg_salary"] = stats["total_net"] / stats["employee_count"]

    return {
        "report_type": "summary",
        "period": f"{month}/{year}",
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_employees": total_employees,
            "total_gross_pay": total_gross,
            "total_net_pay": total_net,
            "total_deductions": total_deductions,
            "average_salary": total_net / total_employees if total_employees else 0,
        },
        "department_stats": dept_stats,
    }


def generate_detailed_report(
    payroll_records: List[PayrollRecordDocument],
    month: int,
    year: int,
    employee_map: Dict[PydanticObjectId, EmployeeDocument],
    department_map: Dict[PydanticObjectId, DepartmentDocument],
) -> Dict[str, Any]:
    detailed = []
    for record in payroll_records:
        employee = employee_map.get(record.employee_id)
        dept_name = _department_name_for_employee(employee, department_map)
        detailed.append(
            {
                "employee_id": employee.employee_id if employee else None,
                "employee_name": _employee_display(employee),
                "department": dept_name,
                "basic_salary": float(record.basic_salary or Decimal("0")),
                "allowances": float(record.total_allowances or Decimal("0")),
                "bonuses": float(record.total_bonuses or Decimal("0")),
                "overtime": float(record.total_overtime or Decimal("0")),
                "gross_pay": float(record.gross_pay or Decimal("0")),
                "deductions": float(record.total_deductions or Decimal("0")),
                "net_pay": float(record.net_pay or Decimal("0")),
                "status": record.status.value if isinstance(record.status, PayrollStatus) else record.status,
                "hours_worked": record.total_hours,
            }
        )

    return {
        "report_type": "detailed",
        "period": f"{month}/{year}",
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": len(detailed),
        "records": detailed,
    }


def generate_tax_report(
    payroll_records: List[PayrollRecordDocument],
    month: int,
    year: int,
) -> Dict[str, Any]:
    total_tax = sum(float(record.total_taxes or Decimal("0")) for record in payroll_records)
    total_insurance = sum(float(record.total_insurance or Decimal("0")) for record in payroll_records)
    total_pension = sum(float(record.total_pension or Decimal("0")) for record in payroll_records)

    tax_brackets = {
        "low": {"count": 0, "total_tax": 0.0},
        "medium": {"count": 0, "total_tax": 0.0},
        "high": {"count": 0, "total_tax": 0.0},
    }
    for record in payroll_records:
        annual_salary = float(record.basic_salary or Decimal("0")) * 12
        if annual_salary < 50000:
            bracket = "low"
        elif annual_salary < 100000:
            bracket = "medium"
        else:
            bracket = "high"
        tax_brackets[bracket]["count"] += 1
        tax_brackets[bracket]["total_tax"] += float(record.total_taxes or Decimal("0"))

    return {
        "report_type": "tax",
        "period": f"{month}/{year}",
        "generated_at": datetime.utcnow().isoformat(),
        "tax_summary": {
            "total_income_tax": total_tax,
            "total_insurance": total_insurance,
            "total_pension": total_pension,
            "total_tax_liability": total_tax + total_insurance + total_pension,
        },
        "tax_brackets": tax_brackets,
    }


def generate_benefits_report(
    payroll_records: List[PayrollRecordDocument],
    month: int,
    year: int,
) -> Dict[str, Any]:
    total_allowances = sum(float(record.total_allowances or Decimal("0")) for record in payroll_records)
    total_bonuses = sum(float(record.total_bonuses or Decimal("0")) for record in payroll_records)
    total_overtime = sum(float(record.total_overtime or Decimal("0")) for record in payroll_records)
    total_insurance = sum(float(record.total_insurance or Decimal("0")) for record in payroll_records)
    total_pension = sum(float(record.total_pension or Decimal("0")) for record in payroll_records)

    return {
        "report_type": "benefits",
        "period": f"{month}/{year}",
        "generated_at": datetime.utcnow().isoformat(),
        "benefits_summary": {
            "total_allowances": total_allowances,
            "total_bonuses": total_bonuses,
            "total_overtime": total_overtime,
            "total_insurance": total_insurance,
            "total_pension": total_pension,
            "total_benefits": total_allowances + total_bonuses + total_overtime + total_insurance + total_pension,
        },
    }
