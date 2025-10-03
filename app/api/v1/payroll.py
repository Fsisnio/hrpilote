from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.payroll import PayrollRecord, PayrollPeriod, PayrollStatus, PayrollComponent, SalaryComponentType, PayPeriodType, PayrollSettings
from app.models.employee import Employee
from app.models.organization import Organization
from app.models.department import Department
from app.api.v1.auth import get_current_user
from app.utils.pdf_generator import generate_payroll_pdf
from app.schemas.payroll import PayrollRecordUpdate, PayrollRecordCreate, PayrollSettingsUpdate, PayrollSettingsResponse
from datetime import datetime, date
from typing import List, Optional
from decimal import Decimal
import json
import logging

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


def recalculate_payroll_period_totals(db: Session, payroll_period_id: int):
    """
    Recalculate and update payroll period totals based on all records in the period
    """
    try:
        # Get all payroll records for this period
        records = db.query(PayrollRecord).filter(
            PayrollRecord.payroll_period_id == payroll_period_id
        ).all()
        
        # Calculate totals
        total_gross = sum(float(record.gross_pay) for record in records)
        total_net = sum(float(record.net_pay) for record in records)
        total_deductions = total_gross - total_net
        
        # Get the payroll period and update totals
        payroll_period = db.query(PayrollPeriod).filter(
            PayrollPeriod.id == payroll_period_id
        ).first()
        
        if payroll_period:
            payroll_period.total_gross_pay = Decimal(str(total_gross))
            payroll_period.total_net_pay = Decimal(str(total_net))
            payroll_period.total_deductions = Decimal(str(total_deductions))
            
            logger.info(f"🔄 Updated payroll period {payroll_period_id} totals: "
                       f"Gross={total_gross}, Net={total_net}, Deductions={total_deductions}")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"❌ Error recalculating payroll period totals: {str(e)}")
        db.rollback()
        raise


@router.post("/process")
async def process_payroll(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process payroll for all active employees
    """
    try:
        # Check if user has permission
        if current_user.role not in [UserRole.HR, UserRole.PAYROLL, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to process payroll"
            )
        
        # Get user's organization
        if current_user.role == UserRole.SUPER_ADMIN:
            org_filter = True
        else:
            org_filter = Employee.organization_id == current_user.organization_id
        
        # Get all active employees
        employees = db.query(Employee).filter(
            and_(
                org_filter,
                Employee.status == "ACTIVE"
            )
        ).all()
        
        if not employees:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active employees found"
            )
        
        # Create payroll period for current month
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Check if payroll period already exists
        if current_user.role == UserRole.SUPER_ADMIN:
            period_filter = True
        else:
            period_filter = PayrollPeriod.organization_id == current_user.organization_id
            
        existing_period = db.query(PayrollPeriod).filter(
            and_(
                period_filter,
                func.extract('month', PayrollPeriod.start_date) == current_month,
                func.extract('year', PayrollPeriod.start_date) == current_year
            )
        ).first()
        
        if existing_period:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payroll for {current_month}/{current_year} already processed"
            )
        
        # Create new payroll period
        # Calculate end date and pay date properly
        if current_month < 12:
            end_date = date(current_year, current_month + 1, 1)
            pay_date = date(current_year, current_month + 1, 1)
        else:
            end_date = date(current_year + 1, 1, 1)
            pay_date = date(current_year + 1, 1, 1)
            
        payroll_period = PayrollPeriod(
            organization_id=current_user.organization_id,
            name=f"Payroll Period {current_month}/{current_year}",
            period_type="MONTHLY",
            start_date=date(current_year, current_month, 1),
            end_date=end_date,
            pay_date=pay_date,
            processing_date=date.today(),
            status=PayrollStatus.PROCESSING
        )
        
        db.add(payroll_period)
        db.flush()
        
        processed_count = 0
        total_gross = Decimal('0')
        total_net = Decimal('0')
        
        # Process payroll for each employee
        for employee in employees:
            # Calculate basic salary (annual to monthly)
            base_salary = employee.base_salary or Decimal('50000')
            monthly_salary = base_salary / 12
            
            # Calculate allowances (example: 10% of base salary)
            allowances = monthly_salary * Decimal('0.10')
            
            # Calculate additional allocations
            housing_allowance = monthly_salary * Decimal('0.05')  # 5% for housing
            transport_allowance = Decimal('2000')  # Fixed transport allowance
            medical_allowance = Decimal('1500')  # Fixed medical allowance
            meal_allowance = Decimal('1000')  # Fixed meal allowance
            
            # Calculate deductions (example: 20% for taxes and benefits)
            deductions = monthly_salary * Decimal('0.20')
            
            # Calculate additional deductions
            loan_deduction = Decimal('5000')  # Fixed loan deduction
            advance_deduction = Decimal('2000')  # Fixed advance deduction
            uniform_deduction = Decimal('500')  # Fixed uniform deduction
            parking_deduction = Decimal('300')  # Fixed parking deduction
            late_penalty = Decimal('0')  # No late penalty by default
            
            # Calculate total allocations and deductions
            total_allocations = allowances + housing_allowance + transport_allowance + medical_allowance + meal_allowance
            total_additional_deductions = loan_deduction + advance_deduction + uniform_deduction + parking_deduction + late_penalty
            
            # Calculate net pay
            gross_pay = monthly_salary + total_allocations
            net_pay = gross_pay - deductions - total_additional_deductions
            
            # Create payroll record
            payroll_record = PayrollRecord(
                payroll_period_id=payroll_period.id,
                employee_id=employee.id,
                organization_id=employee.organization_id,
                base_salary=monthly_salary,
                basic_salary=monthly_salary,
                total_earnings=monthly_salary,
                total_allowances=total_allocations,
                total_bonuses=Decimal('0'),
                total_overtime=Decimal('0'),
                total_commission=Decimal('0'),
                total_deductions=deductions + total_additional_deductions,
                total_taxes=deductions * Decimal('0.8'),
                total_insurance=deductions * Decimal('0.1'),
                total_pension=deductions * Decimal('0.1'),
                gross_pay=gross_pay,
                net_pay=net_pay,
                regular_hours=160.0,
                overtime_hours=0.0,
                total_hours=160.0,
                status=PayrollStatus.PROCESSING,
                is_approved=False,
                notes=f"Auto-processed payroll for {employee.full_name}"
            )
            
            db.add(payroll_record)
            db.flush()  # Flush to get the payroll_record.id
            
            # Create salary components
            components = [
                # Basic salary
                {
                    'name': 'Basic Salary',
                    'component_type': 'BASIC',
                    'amount': monthly_salary,
                    'is_taxable': True
                },
                # Original allowance
                {
                    'name': 'Monthly Allowance',
                    'component_type': 'ALLOWANCE',
                    'amount': allowances,
                    'is_taxable': True
                },
                # New allocation entries
                {
                    'name': 'Housing Allowance',
                    'component_type': 'HOUSING_ALLOWANCE',
                    'amount': housing_allowance,
                    'is_taxable': True
                },
                {
                    'name': 'Transport Allowance',
                    'component_type': 'TRANSPORT_ALLOWANCE',
                    'amount': transport_allowance,
                    'is_taxable': True
                },
                {
                    'name': 'Medical Allowance',
                    'component_type': 'MEDICAL_ALLOWANCE',
                    'amount': medical_allowance,
                    'is_taxable': True
                },
                {
                    'name': 'Meal Allowance',
                    'component_type': 'MEAL_ALLOWANCE',
                    'amount': meal_allowance,
                    'is_taxable': True
                },
                # Original deductions
                {
                    'name': 'Income Tax',
                    'component_type': 'TAX',
                    'amount': -deductions * Decimal('0.8'),
                    'is_taxable': False
                },
                {
                    'name': 'Health Insurance',
                    'component_type': 'INSURANCE',
                    'amount': -deductions * Decimal('0.1'),
                    'is_taxable': False
                },
                {
                    'name': 'Pension Contribution',
                    'component_type': 'PENSION',
                    'amount': -deductions * Decimal('0.1'),
                    'is_taxable': False
                },
                # New deduction entries
                {
                    'name': 'Loan Deduction',
                    'component_type': 'LOAN_DEDUCTION',
                    'amount': -loan_deduction,
                    'is_taxable': False
                },
                {
                    'name': 'Advance Deduction',
                    'component_type': 'ADVANCE_DEDUCTION',
                    'amount': -advance_deduction,
                    'is_taxable': False
                },
                {
                    'name': 'Uniform Deduction',
                    'component_type': 'UNIFORM_DEDUCTION',
                    'amount': -uniform_deduction,
                    'is_taxable': False
                },
                {
                    'name': 'Parking Deduction',
                    'component_type': 'PARKING_DEDUCTION',
                    'amount': -parking_deduction,
                    'is_taxable': False
                },
                {
                    'name': 'Late Penalty',
                    'component_type': 'LATE_PENALTY',
                    'amount': -late_penalty,
                    'is_taxable': False
                }
            ]
            
            for comp_data in components:
                component = PayrollComponent(
                    payroll_record_id=payroll_record.id,
                    name=comp_data['name'],
                    component_type=comp_data['component_type'],
                    amount=comp_data['amount'],
                    is_taxable=comp_data['is_taxable'],
                    description=f"{comp_data['name']} for {employee.full_name}"
                )
                db.add(component)
            
            processed_count += 1
            total_gross += gross_pay
            total_net += net_pay
        
        # Update payroll period totals
        payroll_period.total_gross_pay = total_gross
        payroll_period.total_net_pay = total_net
        payroll_period.total_deductions = total_gross - total_net
        
        db.commit()
        
        return {
            "message": f"Payroll processed successfully for {processed_count} employees",
            "processed_count": processed_count,
            "total_gross_pay": float(total_gross),
            "total_net_pay": float(total_net),
            "period_id": payroll_period.id
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like "already processed") as-is
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_details = traceback.format_exc()
        print(f"Payroll processing error: {str(e)}")
        print(f"Error details: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing payroll: {str(e)}"
        )


@router.post("/generate-report")
async def generate_payroll_report(
    report_type: str = Query(..., description="Type of report: summary, detailed, tax, benefits"),
    month: Optional[int] = Query(None, description="Month (1-12)"),
    year: Optional[int] = Query(None, description="Year"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate payroll reports
    """
    # Check if user has permission
    if current_user.role not in [UserRole.HR, UserRole.PAYROLL, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to generate reports"
        )
    
    try:
        # Get user's organization
        if current_user.role == UserRole.SUPER_ADMIN:
            org_filter = True
        else:
            org_filter = Employee.organization_id == current_user.organization_id
        
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No payroll records found for {month}/{year}"
            )
        
        # Generate report based on type
        if report_type == "summary":
            report_data = generate_summary_report(payroll_records, month, year)
        elif report_type == "detailed":
            report_data = generate_detailed_report(payroll_records, month, year)
        elif report_type == "tax":
            report_data = generate_tax_report(payroll_records, month, year)
        elif report_type == "benefits":
            report_data = generate_benefits_report(payroll_records, month, year)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid report type. Use: summary, detailed, tax, or benefits"
            )
        
        return report_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )


@router.get("/download-pdf")
async def download_payroll_pdf(
    report_type: str = Query(..., description="Type of report: summary, detailed, tax, benefits"),
    month: Optional[int] = Query(None, description="Month (1-12)"),
    year: Optional[int] = Query(None, description="Year"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download payroll report as PDF
    """
    # Check if user has permission
    if current_user.role not in [UserRole.HR, UserRole.PAYROLL, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to download reports"
        )
    
    try:
        # Get user's organization
        if current_user.role == UserRole.SUPER_ADMIN:
            org_filter = True
        else:
            org_filter = Employee.organization_id == current_user.organization_id
        
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No payroll records found for {month}/{year}"
            )
        
        # Generate report data based on type
        if report_type == "summary":
            report_data = generate_summary_report(payroll_records, month, year)
        elif report_type == "detailed":
            report_data = generate_detailed_report(payroll_records, month, year)
        elif report_type == "tax":
            report_data = generate_tax_report(payroll_records, month, year)
        elif report_type == "benefits":
            report_data = generate_benefits_report(payroll_records, month, year)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid report type. Use: summary, detailed, tax, or benefits"
            )
        
        # Generate PDF
        pdf_buffer = generate_payroll_pdf(report_type, report_data)
        
        # Create filename
        month_name = datetime(year, month, 1).strftime("%B")
        filename = f"payroll_{report_type}_report_{month_name}_{year}.pdf"
        
        # Return PDF as streaming response
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pdf_buffer.getvalue()))
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF: {str(e)}"
        )


def generate_summary_report(payroll_records: List[PayrollRecord], month: int, year: int) -> dict:
    """Generate summary payroll report"""
    total_employees = len(payroll_records)
    total_gross = sum(float(record.gross_pay) for record in payroll_records)
    total_net = sum(float(record.net_pay) for record in payroll_records)
    total_deductions = sum(float(record.total_deductions) for record in payroll_records)
    
    # Group by department
    dept_stats = {}
    for record in payroll_records:
        dept_name = record.employee.department.name if record.employee.department else "No Department"
        if dept_name not in dept_stats:
            dept_stats[dept_name] = {
                "employee_count": 0,
                "total_gross": 0,
                "total_net": 0,
                "avg_salary": 0
            }
        
        dept_stats[dept_name]["employee_count"] += 1
        dept_stats[dept_name]["total_gross"] += float(record.gross_pay)
        dept_stats[dept_name]["total_net"] += float(record.net_pay)
    
    # Calculate averages
    for dept in dept_stats.values():
        dept["avg_salary"] = dept["total_net"] / dept["employee_count"]
    
    return {
        "report_type": "summary",
        "period": f"{month}/{year}",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_employees": total_employees,
            "total_gross_pay": total_gross,
            "total_net_pay": total_net,
            "total_deductions": total_deductions,
            "average_salary": total_net / total_employees if total_employees > 0 else 0
        },
        "department_stats": dept_stats
    }


def generate_detailed_report(payroll_records: List[PayrollRecord], month: int, year: int) -> dict:
    """Generate detailed payroll report"""
    detailed_records = []
    
    for record in payroll_records:
        detailed_records.append({
            "employee_id": record.employee.employee_id,
            "employee_name": record.employee.full_name,
            "department": record.employee.department.name if record.employee.department else "No Department",
            "basic_salary": float(record.basic_salary),
            "allowances": float(record.total_allowances),
            "bonuses": float(record.total_bonuses),
            "overtime": float(record.total_overtime),
            "gross_pay": float(record.gross_pay),
            "deductions": float(record.total_deductions),
            "net_pay": float(record.net_pay),
            "status": record.status.value,
            "hours_worked": record.total_hours
        })
    
    return {
        "report_type": "detailed",
        "period": f"{month}/{year}",
        "generated_at": datetime.now().isoformat(),
        "total_records": len(detailed_records),
        "records": detailed_records
    }


def generate_tax_report(payroll_records: List[PayrollRecord], month: int, year: int) -> dict:
    """Generate tax report"""
    total_tax = sum(float(record.total_taxes) for record in payroll_records)
    total_insurance = sum(float(record.total_insurance) for record in payroll_records)
    total_pension = sum(float(record.total_pension) for record in payroll_records)
    
    # Tax brackets analysis (simplified)
    tax_brackets = {
        "low": {"count": 0, "total_tax": 0},
        "medium": {"count": 0, "total_tax": 0},
        "high": {"count": 0, "total_tax": 0}
    }
    
    for record in payroll_records:
        annual_salary = float(record.basic_salary) * 12
        if annual_salary < 50000:
            tax_brackets["low"]["count"] += 1
            tax_brackets["low"]["total_tax"] += float(record.total_taxes)
        elif annual_salary < 100000:
            tax_brackets["medium"]["count"] += 1
            tax_brackets["medium"]["total_tax"] += float(record.total_taxes)
        else:
            tax_brackets["high"]["count"] += 1
            tax_brackets["high"]["total_tax"] += float(record.total_taxes)
    
    return {
        "report_type": "tax",
        "period": f"{month}/{year}",
        "generated_at": datetime.now().isoformat(),
        "tax_summary": {
            "total_income_tax": total_tax,
            "total_insurance": total_insurance,
            "total_pension": total_pension,
            "total_tax_liability": total_tax + total_insurance + total_pension
        },
        "tax_brackets": tax_brackets
    }


def generate_benefits_report(payroll_records: List[PayrollRecord], month: int, year: int) -> dict:
    """Generate benefits report"""
    total_allowances = sum(float(record.total_allowances) for record in payroll_records)
    total_bonuses = sum(float(record.total_bonuses) for record in payroll_records)
    total_overtime = sum(float(record.total_overtime) for record in payroll_records)
    total_insurance = sum(float(record.total_insurance) for record in payroll_records)
    total_pension = sum(float(record.total_pension) for record in payroll_records)
    
    return {
        "report_type": "benefits",
        "period": f"{month}/{year}",
        "generated_at": datetime.now().isoformat(),
        "benefits_summary": {
            "total_allowances": total_allowances,
            "total_bonuses": total_bonuses,
            "total_overtime": total_overtime,
            "total_insurance": total_insurance,
            "total_pension": total_pension,
            "total_benefits": total_allowances + total_bonuses + total_overtime + total_insurance + total_pension
        }
    }


@router.get("/summary")
async def get_payroll_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payroll summary statistics
    """
    # Get user's organization
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can see all organizations
        org_filter = True
    else:
        org_filter = Employee.organization_id == current_user.organization_id

    # Get total employees
    total_employees = db.query(Employee).filter(org_filter).count()
    
    # Get current month's payroll data
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Get total payroll for current month (only PAID records)
    current_payroll = db.query(
        func.sum(PayrollRecord.gross_pay).label('total_gross'),
        func.sum(PayrollRecord.net_pay).label('total_net'),
        func.avg(PayrollRecord.net_pay).label('avg_salary')
    ).join(Employee).filter(
        and_(
            org_filter,
            func.extract('month', PayrollRecord.created_at) == current_month,
            func.extract('year', PayrollRecord.created_at) == current_year,
            PayrollRecord.status == PayrollStatus.PAID
        )
    ).first()
    
    # Get pending payments count
    pending_payments = db.query(PayrollRecord).join(Employee).filter(
        and_(
            org_filter,
            PayrollRecord.status == PayrollStatus.PROCESSING
        )
    ).count()
    
    # Get processed payments count
    processed_payments = db.query(PayrollRecord).join(Employee).filter(
        and_(
            org_filter,
            PayrollRecord.status == PayrollStatus.PAID
        )
    ).count()
    
    return {
        "total_employees": total_employees,
        "total_payroll": float(current_payroll.total_gross or 0),
        "average_salary": float(current_payroll.avg_salary or 0),
        "pending_payments": pending_payments,
        "processed_payments": processed_payments
    }


@router.get("/records")
async def get_payroll_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    department: Optional[str] = Query(None)
):
    """
    Get payroll records with filtering and pagination
    """
    # Get user's organization
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can see all organizations
        org_filter = True
    else:
        org_filter = Employee.organization_id == current_user.organization_id
    
    # Build query
    query = db.query(PayrollRecord).join(Employee).filter(org_filter)
    
    # Apply filters
    if status:
        query = query.filter(PayrollRecord.status == status)
    
    if department:
        query = query.join(Department, Employee.department_id == Department.id).filter(Department.name == department)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and get records
    records = query.offset(skip).limit(limit).all()
    
    # Format response
    payroll_records = []
    for record in records:
        # Get components
        components = db.query(PayrollComponent).filter(
            PayrollComponent.payroll_record_id == record.id
        ).all()
        
        # Calculate totals including new allocation and deduction types
        allowances = sum(float(c.amount) for c in components if c.component_type in [
            SalaryComponentType.ALLOWANCE, SalaryComponentType.BONUS, SalaryComponentType.OVERTIME, SalaryComponentType.COMMISSION,
            SalaryComponentType.HOUSING_ALLOWANCE, SalaryComponentType.TRANSPORT_ALLOWANCE, SalaryComponentType.MEDICAL_ALLOWANCE, SalaryComponentType.MEAL_ALLOWANCE
        ])
        deductions = sum(float(c.amount) for c in components if c.component_type in [
            SalaryComponentType.DEDUCTION, SalaryComponentType.TAX, SalaryComponentType.INSURANCE, SalaryComponentType.PENSION,
            SalaryComponentType.LOAN_DEDUCTION, SalaryComponentType.ADVANCE_DEDUCTION, SalaryComponentType.UNIFORM_DEDUCTION, SalaryComponentType.PARKING_DEDUCTION, SalaryComponentType.LATE_PENALTY
        ])
        
        # Get individual allocation and deduction amounts
        housing_allowance = next((float(c.amount) for c in components if c.component_type == SalaryComponentType.HOUSING_ALLOWANCE), 0)
        transport_allowance = next((float(c.amount) for c in components if c.component_type == SalaryComponentType.TRANSPORT_ALLOWANCE), 0)
        medical_allowance = next((float(c.amount) for c in components if c.component_type == SalaryComponentType.MEDICAL_ALLOWANCE), 0)
        meal_allowance = next((float(c.amount) for c in components if c.component_type == SalaryComponentType.MEAL_ALLOWANCE), 0)
        
        loan_deduction = next((float(c.amount) for c in components if c.component_type == SalaryComponentType.LOAN_DEDUCTION), 0)
        advance_deduction = next((float(c.amount) for c in components if c.component_type == SalaryComponentType.ADVANCE_DEDUCTION), 0)
        uniform_deduction = next((float(c.amount) for c in components if c.component_type == SalaryComponentType.UNIFORM_DEDUCTION), 0)
        parking_deduction = next((float(c.amount) for c in components if c.component_type == SalaryComponentType.PARKING_DEDUCTION), 0)
        late_penalty = next((float(c.amount) for c in components if c.component_type == SalaryComponentType.LATE_PENALTY), 0)
        
        # Get department name
        department_name = record.employee.department.name if record.employee.department else "No Department"
        
        payroll_records.append({
            "id": record.id,
            "employee": record.employee.full_name,
            "employee_id": record.employee.employee_id,
            "department": department_name,
            "basic_salary": float(record.basic_salary),
            "allowances": allowances,
            "deductions": deductions,
            "net_salary": float(record.net_pay),
            "status": record.status.value,
            "pay_date": record.created_at.date().isoformat() if record.created_at else None,
            
            # New allocation fields
            "housing_allowance": housing_allowance,
            "transport_allowance": transport_allowance,
            "medical_allowance": medical_allowance,
            "meal_allowance": meal_allowance,
            
            # New deduction fields
            "loan_deduction": loan_deduction,
            "advance_deduction": advance_deduction,
            "uniform_deduction": uniform_deduction,
            "parking_deduction": parking_deduction,
            "late_penalty": late_penalty
        })
    
    return {
        "records": payroll_records,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/records")
async def create_payroll_record(
    record_data: PayrollRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new payroll record
    """
    # Check if user has permission
    if current_user.role not in [UserRole.HR, UserRole.PAYROLL, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create payroll records"
        )
    
    try:
        # Verify employee exists and user has access
        employee = db.query(Employee).filter(Employee.id == record_data.employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Check if user has access to this employee
        if current_user.role != UserRole.SUPER_ADMIN and employee.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this employee"
            )
        
        # Ensure there's an active payroll period for the employee's org and current month
        current_month = datetime.now().month
        current_year = datetime.now().year

        period = db.query(PayrollPeriod).filter(
            and_(
                PayrollPeriod.organization_id == employee.organization_id,
                func.extract('month', PayrollPeriod.start_date) == current_month,
                func.extract('year', PayrollPeriod.start_date) == current_year
            )
        ).first()

        if not period:
            # Create a monthly period that spans the current month
            start_date = date(current_year, current_month, 1)
            end_date = date(current_year + (1 if current_month == 12 else 0), (1 if current_month == 12 else current_month + 1), 1)
            period = PayrollPeriod(
                organization_id=employee.organization_id,
                name=f"Payroll Period {current_month}/{current_year}",
                period_type=PayPeriodType.MONTHLY,
                start_date=start_date,
                end_date=end_date,
                pay_date=end_date,
                processing_date=date.today(),
                status=PayrollStatus.PROCESSING
            )
            db.add(period)
            db.flush()

        # Create payroll record
        payroll_record = PayrollRecord(
            payroll_period_id=period.id,
            employee_id=record_data.employee_id,
            organization_id=employee.organization_id,
            base_salary=Decimal(str(record_data.basic_salary)),
            basic_salary=Decimal(str(record_data.basic_salary)),
            total_earnings=Decimal(str(record_data.basic_salary)),
            total_allowances=Decimal('0'),
            total_bonuses=Decimal('0'),
            total_overtime=Decimal('0'),
            total_commission=Decimal('0'),
            total_deductions=Decimal('0'),
            total_taxes=Decimal('0'),
            total_insurance=Decimal('0'),
            total_pension=Decimal('0'),
            gross_pay=Decimal(str(record_data.basic_salary)),
            net_pay=Decimal(str(record_data.basic_salary)),
            regular_hours=160.0,
            overtime_hours=0.0,
            total_hours=160.0,
            status=record_data.status,
            is_approved=False,
            notes=record_data.notes or f"Manual payroll record for {employee.full_name}"
        )
        
        db.add(payroll_record)
        db.flush()  # Get the ID
        
        # Create salary components
        components_to_create = {
            'housing_allowance': ('HOUSING_ALLOWANCE', record_data.housing_allowance, True),
            'transport_allowance': ('TRANSPORT_ALLOWANCE', record_data.transport_allowance, True),
            'medical_allowance': ('MEDICAL_ALLOWANCE', record_data.medical_allowance, True),
            'meal_allowance': ('MEAL_ALLOWANCE', record_data.meal_allowance, True),
            'loan_deduction': ('LOAN_DEDUCTION', record_data.loan_deduction, False),
            'advance_deduction': ('ADVANCE_DEDUCTION', record_data.advance_deduction, False),
            'uniform_deduction': ('UNIFORM_DEDUCTION', record_data.uniform_deduction, False),
            'parking_deduction': ('PARKING_DEDUCTION', record_data.parking_deduction, False),
            'late_penalty': ('LATE_PENALTY', record_data.late_penalty, False)
        }
        
        for field, (component_type, amount, is_taxable) in components_to_create.items():
            if amount and amount > 0:
                # Store deductions as negative values
                if 'deduction' in field or 'penalty' in field:
                    stored_amount = Decimal(str(-amount))  # Make deductions negative
                else:
                    stored_amount = Decimal(str(amount))   # Keep allowances positive
                
                component = PayrollComponent(
                    payroll_record_id=payroll_record.id,
                    name=field.replace('_', ' ').title(),
                    component_type=component_type,
                    amount=stored_amount,
                    is_taxable=is_taxable,
                    description=f"{field.replace('_', ' ').title()} for {employee.full_name}"
                )
                db.add(component)
        
        # Recalculate totals
        all_components = db.query(PayrollComponent).filter(
            PayrollComponent.payroll_record_id == payroll_record.id
        ).all()
        
        total_allowances = sum(float(c.amount) for c in all_components if c.component_type in [
            SalaryComponentType.ALLOWANCE, SalaryComponentType.BONUS, SalaryComponentType.OVERTIME, SalaryComponentType.COMMISSION,
            SalaryComponentType.HOUSING_ALLOWANCE, SalaryComponentType.TRANSPORT_ALLOWANCE, SalaryComponentType.MEDICAL_ALLOWANCE, SalaryComponentType.MEAL_ALLOWANCE
        ])
        total_deductions = sum(float(c.amount) for c in all_components if c.component_type in [
            SalaryComponentType.DEDUCTION, SalaryComponentType.TAX, SalaryComponentType.INSURANCE, SalaryComponentType.PENSION,
            SalaryComponentType.LOAN_DEDUCTION, SalaryComponentType.ADVANCE_DEDUCTION, SalaryComponentType.UNIFORM_DEDUCTION, SalaryComponentType.PARKING_DEDUCTION, SalaryComponentType.LATE_PENALTY
        ])
        
        payroll_record.total_allowances = Decimal(str(total_allowances))
        payroll_record.total_deductions = Decimal(str(abs(total_deductions)))  # Use absolute value for deductions
        payroll_record.gross_pay = payroll_record.basic_salary + payroll_record.total_allowances
        payroll_record.net_pay = payroll_record.gross_pay - payroll_record.total_deductions
        
        db.commit()
        db.refresh(payroll_record)
        
        # Get updated components for response
        updated_components = db.query(PayrollComponent).filter(
            PayrollComponent.payroll_record_id == payroll_record.id
        ).all()
        
        # Calculate totals for response
        allowances = sum(float(c.amount) for c in updated_components if c.component_type in [
            SalaryComponentType.ALLOWANCE, SalaryComponentType.BONUS, SalaryComponentType.OVERTIME, SalaryComponentType.COMMISSION,
            SalaryComponentType.HOUSING_ALLOWANCE, SalaryComponentType.TRANSPORT_ALLOWANCE, SalaryComponentType.MEDICAL_ALLOWANCE, SalaryComponentType.MEAL_ALLOWANCE
        ])
        deductions = sum(float(c.amount) for c in updated_components if c.component_type in [
            SalaryComponentType.DEDUCTION, SalaryComponentType.TAX, SalaryComponentType.INSURANCE, SalaryComponentType.PENSION,
            SalaryComponentType.LOAN_DEDUCTION, SalaryComponentType.ADVANCE_DEDUCTION, SalaryComponentType.UNIFORM_DEDUCTION, SalaryComponentType.PARKING_DEDUCTION, SalaryComponentType.LATE_PENALTY
        ])
        
        # Get individual allocation and deduction amounts
        housing_allowance = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.HOUSING_ALLOWANCE), 0)
        transport_allowance = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.TRANSPORT_ALLOWANCE), 0)
        medical_allowance = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.MEDICAL_ALLOWANCE), 0)
        meal_allowance = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.MEAL_ALLOWANCE), 0)
        
        loan_deduction = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.LOAN_DEDUCTION), 0)
        advance_deduction = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.ADVANCE_DEDUCTION), 0)
        uniform_deduction = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.UNIFORM_DEDUCTION), 0)
        parking_deduction = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.PARKING_DEDUCTION), 0)
        late_penalty = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.LATE_PENALTY), 0)
        
        # Get department name
        department_name = employee.department.name if employee.department else "No Department"
        
        # Recalculate payroll period totals after creating the record
        try:
            recalculate_payroll_period_totals(db, payroll_record.payroll_period_id)
        except Exception as e:
            logger.error(f"⚠️ Warning: Failed to recalculate payroll period totals: {str(e)}")
            # Don't fail the entire operation if period totals recalculation fails
        
        return {
            "message": "Payroll record created successfully",
            "record_id": payroll_record.id,
            "created_record": {
                "id": payroll_record.id,
                "employee": employee.full_name,
                "employee_id": employee.employee_id,
                "department": department_name,
                "basic_salary": float(payroll_record.basic_salary),
                "allowances": allowances,
                "deductions": deductions,
                "net_salary": float(payroll_record.net_pay),
                "status": payroll_record.status.value,
                "pay_date": payroll_record.created_at.date().isoformat() if payroll_record.created_at else None,
                
                # New allocation fields
                "housing_allowance": housing_allowance,
                "transport_allowance": transport_allowance,
                "medical_allowance": medical_allowance,
                "meal_allowance": meal_allowance,
                
                # New deduction fields
                "loan_deduction": loan_deduction,
                "advance_deduction": advance_deduction,
                "uniform_deduction": uniform_deduction,
                "parking_deduction": parking_deduction,
                "late_penalty": late_penalty
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating payroll record: {str(e)}"
        )


@router.put("/records/{record_id}")
async def update_payroll_record(
    record_id: int,
    record_data: PayrollRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a payroll record
    """
    # Check if user has permission
    if current_user.role not in [UserRole.HR, UserRole.PAYROLL, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update payroll records"
        )
    
    try:
        logger.info(f"🔄 Starting payroll record update for record_id: {record_id}")
        logger.info(f"📊 Received data: {record_data}")
        
        # Get the payroll record
        record = db.query(PayrollRecord).filter(PayrollRecord.id == record_id).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payroll record not found"
            )
        
        # Check if user has access to this record
        if current_user.role != UserRole.SUPER_ADMIN and record.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this payroll record"
            )
        
        # Update basic fields with validation
        if record_data.basic_salary is not None:
            if record_data.basic_salary < 0:
                raise ValueError("Basic salary cannot be negative")
            record.basic_salary = Decimal(str(record_data.basic_salary))
        
        if record_data.status is not None:
            record.status = record_data.status
        
        # Import the enum for component types
        from app.models.payroll import SalaryComponentType
        
        # Clear existing components for the specific types we're updating
        component_types_to_clear = [
            SalaryComponentType.HOUSING_ALLOWANCE,
            SalaryComponentType.TRANSPORT_ALLOWANCE, 
            SalaryComponentType.MEDICAL_ALLOWANCE,
            SalaryComponentType.MEAL_ALLOWANCE,
            SalaryComponentType.LOAN_DEDUCTION,
            SalaryComponentType.ADVANCE_DEDUCTION,
            SalaryComponentType.UNIFORM_DEDUCTION,
            SalaryComponentType.PARKING_DEDUCTION,
            SalaryComponentType.LATE_PENALTY
        ]
        
        # Delete existing components of these types
        db.query(PayrollComponent).filter(
            PayrollComponent.payroll_record_id == record_id,
            PayrollComponent.component_type.in_(component_types_to_clear)
        ).delete(synchronize_session=False)
        
        # Update components for new allocation and deduction fields
        components_to_update = {
            'housing_allowance': SalaryComponentType.HOUSING_ALLOWANCE,
            'transport_allowance': SalaryComponentType.TRANSPORT_ALLOWANCE, 
            'medical_allowance': SalaryComponentType.MEDICAL_ALLOWANCE,
            'meal_allowance': SalaryComponentType.MEAL_ALLOWANCE,
            'loan_deduction': SalaryComponentType.LOAN_DEDUCTION,
            'advance_deduction': SalaryComponentType.ADVANCE_DEDUCTION,
            'uniform_deduction': SalaryComponentType.UNIFORM_DEDUCTION,
            'parking_deduction': SalaryComponentType.PARKING_DEDUCTION,
            'late_penalty': SalaryComponentType.LATE_PENALTY
        }
        
        for field, component_type in components_to_update.items():
            field_value = getattr(record_data, field, None)
            if field_value is not None:
                # Validate field values
                if field_value < 0:
                    raise ValueError(f"{field.replace('_', ' ').title()} cannot be negative")
                if field_value > 0:
                    # Store deductions as negative values
                    if 'deduction' in field or 'penalty' in field:
                        amount = Decimal(str(-field_value))  # Make deductions negative
                    else:
                        amount = Decimal(str(field_value))   # Keep allowances positive
                    
                    logger.info(f"🔄 Creating new component for {field} ({component_type}): {amount}")
                    
                    # Create new component (existing ones were already cleared)
                    new_component = PayrollComponent(
                        payroll_record_id=record_id,
                        name=field.replace('_', ' ').title(),
                        component_type=component_type,
                        amount=amount,
                        is_taxable=True if 'allowance' in field else False,
                        description=f"{field.replace('_', ' ').title()} for {record.employee.full_name}"
                    )
                    db.add(new_component)
        
        # Flush changes to ensure all components are updated
        db.flush()
        
        # Recalculate totals
        all_components = db.query(PayrollComponent).filter(
            PayrollComponent.payroll_record_id == record_id
        ).all()
        
        # Debug logging
        logger.info(f"🔍 Debug: Found {len(all_components)} components for record {record_id}")
        for comp in all_components:
            logger.info(f"   Component: {comp.component_type} = {comp.amount}")
        
        total_allowances = sum(float(c.amount) for c in all_components if c.component_type in [
            SalaryComponentType.ALLOWANCE, SalaryComponentType.BONUS, SalaryComponentType.OVERTIME, 
            SalaryComponentType.COMMISSION, SalaryComponentType.HOUSING_ALLOWANCE, 
            SalaryComponentType.TRANSPORT_ALLOWANCE, SalaryComponentType.MEDICAL_ALLOWANCE, 
            SalaryComponentType.MEAL_ALLOWANCE
        ])
        total_deductions = sum(float(c.amount) for c in all_components if c.component_type in [
            SalaryComponentType.DEDUCTION, SalaryComponentType.TAX, SalaryComponentType.INSURANCE, 
            SalaryComponentType.PENSION, SalaryComponentType.LOAN_DEDUCTION, 
            SalaryComponentType.ADVANCE_DEDUCTION, SalaryComponentType.UNIFORM_DEDUCTION, 
            SalaryComponentType.PARKING_DEDUCTION, SalaryComponentType.LATE_PENALTY
        ])
        
        logger.info(f"💰 Debug: Total allowances = {total_allowances}, Total deductions = {total_deductions}")
        
        record.total_allowances = Decimal(str(total_allowances))
        record.total_deductions = Decimal(str(abs(total_deductions)))  # Use absolute value for deductions
        record.gross_pay = record.basic_salary + record.total_allowances
        record.net_pay = record.gross_pay - record.total_deductions
        
        logger.info(f"💵 Debug: Basic salary = {record.basic_salary}")
        logger.info(f"💵 Debug: Gross pay = {record.gross_pay}")
        logger.info(f"💵 Debug: Net pay = {record.net_pay}")
        
        db.commit()
        
        # Refresh the record to get updated data
        db.refresh(record)
        
        # Get updated components for response
        updated_components = db.query(PayrollComponent).filter(
            PayrollComponent.payroll_record_id == record_id
        ).all()
        
        # Calculate totals for response
        allowances = sum(float(c.amount) for c in updated_components if c.component_type in [
            SalaryComponentType.ALLOWANCE, SalaryComponentType.BONUS, SalaryComponentType.OVERTIME, SalaryComponentType.COMMISSION,
            SalaryComponentType.HOUSING_ALLOWANCE, SalaryComponentType.TRANSPORT_ALLOWANCE, SalaryComponentType.MEDICAL_ALLOWANCE, SalaryComponentType.MEAL_ALLOWANCE
        ])
        deductions = sum(float(c.amount) for c in updated_components if c.component_type in [
            SalaryComponentType.DEDUCTION, SalaryComponentType.TAX, SalaryComponentType.INSURANCE, SalaryComponentType.PENSION,
            SalaryComponentType.LOAN_DEDUCTION, SalaryComponentType.ADVANCE_DEDUCTION, SalaryComponentType.UNIFORM_DEDUCTION, SalaryComponentType.PARKING_DEDUCTION, SalaryComponentType.LATE_PENALTY
        ])
        
        # Get individual allocation and deduction amounts
        housing_allowance = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.HOUSING_ALLOWANCE), 0)
        transport_allowance = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.TRANSPORT_ALLOWANCE), 0)
        medical_allowance = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.MEDICAL_ALLOWANCE), 0)
        meal_allowance = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.MEAL_ALLOWANCE), 0)
        
        loan_deduction = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.LOAN_DEDUCTION), 0)
        advance_deduction = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.ADVANCE_DEDUCTION), 0)
        uniform_deduction = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.UNIFORM_DEDUCTION), 0)
        parking_deduction = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.PARKING_DEDUCTION), 0)
        late_penalty = next((float(c.amount) for c in updated_components if c.component_type == SalaryComponentType.LATE_PENALTY), 0)
        
        # Get department name
        department_name = record.employee.department.name if record.employee.department else "No Department"
        
        # Recalculate payroll period totals after updating the record
        try:
            recalculate_payroll_period_totals(db, record.payroll_period_id)
        except Exception as e:
            logger.error(f"⚠️ Warning: Failed to recalculate payroll period totals: {str(e)}")
            # Don't fail the entire operation if period totals recalculation fails
        
        return {
            "message": "Payroll record updated successfully",
            "record_id": record_id,
            "updated_record": {
                "id": record.id,
                "employee": record.employee.full_name,
                "employee_id": record.employee.employee_id,
                "department": department_name,
                "basic_salary": float(record.basic_salary),
                "allowances": allowances,
                "deductions": deductions,
                "net_salary": float(record.net_pay),
                "status": record.status.value,
                "pay_date": record.created_at.date().isoformat() if record.created_at else None,
                
                # New allocation fields
                "housing_allowance": housing_allowance,
                "transport_allowance": transport_allowance,
                "medical_allowance": medical_allowance,
                "meal_allowance": meal_allowance,
                
                # New deduction fields
                "loan_deduction": loan_deduction,
                "advance_deduction": advance_deduction,
                "uniform_deduction": uniform_deduction,
                "parking_deduction": parking_deduction,
                "late_penalty": late_penalty
            }
        }
        
    except ValueError as e:
        db.rollback()
        logger.error(f"❌ Validation error updating payroll record {record_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data provided: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Unexpected error updating payroll record {record_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update payroll record. Please check the data and try again. Error: {str(e)}"
        )


@router.get("/activity")
async def get_payroll_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get recent payroll activity
    """
    # Get user's organization
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can see all organizations
        org_filter = True
    else:
        org_filter = Employee.organization_id == current_user.organization_id
    
    # Get recent payroll records
    records = db.query(PayrollRecord).join(Employee).filter(
        org_filter
    ).order_by(PayrollRecord.created_at.desc()).limit(limit).all()
    
    activities = []
    for record in records:
        activities.append({
            "action": f"Payroll processed for {record.employee.full_name}",
            "date": record.created_at.date().isoformat() if record.created_at else None,
            "status": record.status.value
        })
    
    return activities


@router.get("/departments")
async def get_departments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of departments for filtering
    """
    # Get user's organization
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can see all organizations
        org_filter = True
    else:
        org_filter = Department.organization_id == current_user.organization_id
    
    departments = db.query(Department.name).filter(
        and_(
            org_filter,
            Department.status == "ACTIVE"
        )
    ).distinct().all()
    
    return [dept[0] for dept in departments if dept[0]]


@router.get("/payslips")
async def get_payslips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payslips (placeholder)
    """
    return {"message": "Payslips list"}


@router.get("/payslips/{payslip_id}")
async def get_payslip(
    payslip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific payslip (placeholder)
    """
    return {"message": f"Payslip {payslip_id} details"}


@router.get("/reports")
async def get_payroll_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payroll reports (placeholder)
    """
    return {"message": "Payroll reports"}


# Payroll Settings Endpoints
@router.get("/settings")
async def get_payroll_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payroll settings for the user's organization
    """
    try:
        # Check if user has permission
        if current_user.role not in [UserRole.HR, UserRole.PAYROLL, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view payroll settings"
            )
        
        # Get settings for the user's organization
        settings = db.query(PayrollSettings).filter(
            PayrollSettings.organization_id == current_user.organization_id
        ).first()
        
        # If no settings exist, return default values
        if not settings:
            default_settings = PayrollSettingsResponse(
                id=0,
                organization_id=current_user.organization_id or 0,
                payroll_cycle="Monthly",
                pay_day="Last day of month",
                currency="USD ($)",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            return default_settings
        
        return PayrollSettingsResponse.from_orm(settings)
        
    except Exception as e:
        logger.error(f"❌ Error getting payroll settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting payroll settings: {str(e)}"
        )


@router.put("/settings")
async def update_payroll_settings(
    settings_data: PayrollSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update payroll settings for the user's organization
    """
    try:
        # Check if user has permission
        if current_user.role not in [UserRole.HR, UserRole.PAYROLL, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update payroll settings"
            )
        
        # Ensure the user is scoped to an organization
        if current_user.organization_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update payroll settings: user is not assigned to an organization"
            )

        logger.info(f"🔄 Updating payroll settings for organization {current_user.organization_id}")
        logger.info(f"📊 Settings data: {settings_data}")
        
        # Get existing settings or create new ones
        settings = db.query(PayrollSettings).filter(
            PayrollSettings.organization_id == current_user.organization_id
        ).first()
        
        if settings:
            # Update existing settings
            if settings_data.payroll_cycle is not None:
                settings.payroll_cycle = settings_data.payroll_cycle
            if settings_data.pay_day is not None:
                settings.pay_day = settings_data.pay_day
            if settings_data.currency is not None:
                settings.currency = settings_data.currency
            settings.updated_at = datetime.now()
        else:
            # Create new settings
            settings = PayrollSettings(
                organization_id=current_user.organization_id,
                payroll_cycle=settings_data.payroll_cycle or "Monthly",
                pay_day=settings_data.pay_day or "Last day of month",
                currency=settings_data.currency or "USD ($)"
            )
            db.add(settings)
        
        db.commit()
        db.refresh(settings)
        
        logger.info(f"✅ Payroll settings updated successfully")
        
        return {
            "message": "Payroll settings updated successfully",
            "settings": PayrollSettingsResponse.from_orm(settings)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error updating payroll settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating payroll settings: {str(e)}"
        ) 