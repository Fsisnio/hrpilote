from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import datetime, date
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.employee import Employee
from app.models.expense import Expense, ExpenseItem, ExpenseReport, ExpenseStatus, ExpenseType, PaymentMethod
from app.api.v1.auth import get_current_user

router = APIRouter()


@router.get("/items")
async def get_expense_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    status: Optional[str] = None
):
    """
    Get expense items with organization-specific filtering
    """
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view expense items"
        )
    
    # Set organization filter
    if current_user.role == UserRole.SUPER_ADMIN:
        org_filter = True  # Super admin can see all data
    else:
        org_filter = Expense.organization_id == current_user.organization_id
    
    try:
        # Build query
        query = db.query(ExpenseItem).join(Expense).filter(org_filter)
        
        # Apply filters
        if category:
            query = query.filter(Expense.expense_type == category.upper())
        if status:
            query = query.filter(Expense.status == status.upper())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        items = query.offset(skip).limit(limit).all()
        
        # Format response
        expense_items = []
        for item in items:
            expense_items.append({
                "id": item.id,
                "description": item.description,
                "amount": float(item.amount),
                "category": item.expense.expense_type.value,
                "date": item.expense.expense_date.isoformat(),
                "receipt": item.expense.receipt_number,
                "status": item.expense.status.value,
                "employee_name": f"{item.expense.employee.first_name} {item.expense.employee.last_name}",
                "expense_id": item.expense_id
            })
        
        return {
            "items": expense_items,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching expense items: {str(e)}"
        )


@router.post("/items")
async def create_expense_item(
    item_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new expense item
    """
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create expense items"
        )
    
    try:
        # Get employee record for current user
        employee = db.query(Employee).filter(
            Employee.user_id == current_user.id
        ).first()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee record not found"
            )
        
        # Create expense record first
        expense = Expense(
            employee_id=employee.id,
            organization_id=current_user.organization_id,
            title=item_data.get("title", "Individual Expense Item"),
            description=item_data.get("description", ""),
            expense_type=ExpenseType(item_data.get("category", "OTHER").upper()),
            amount=item_data.get("amount", 0),
            expense_date=datetime.strptime(item_data.get("date", datetime.now().date().isoformat()), "%Y-%m-%d").date(),
            payment_method=PaymentMethod(item_data.get("payment_method", "CASH").upper()),
            status=ExpenseStatus.DRAFT,
            receipt_number=item_data.get("receipt_number"),
            location=item_data.get("location", ""),
            vendor=item_data.get("vendor", "")
        )
        
        db.add(expense)
        db.commit()
        db.refresh(expense)
        
        # Create expense item
        expense_item = ExpenseItem(
            expense_id=expense.id,
            description=item_data.get("description", ""),
            amount=item_data.get("amount", 0),
            category=item_data.get("category", "OTHER"),
            expense_date=expense.expense_date,
            receipt_number=item_data.get("receipt_number")
        )
        
        db.add(expense_item)
        db.commit()
        db.refresh(expense_item)
        
        return {
            "id": expense_item.id,
            "description": expense_item.description,
            "amount": float(expense_item.amount),
            "category": expense_item.category,
            "date": expense_item.expense_date.isoformat(),
            "receipt": expense_item.receipt_number,
            "status": expense.status.value,
            "employee_name": f"{employee.first_name} {employee.last_name}",
            "expense_id": expense_item.expense_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating expense item: {str(e)}"
        )


@router.put("/items/{item_id}")
async def update_expense_item(
    item_id: int,
    item_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an expense item
    """
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update expense items"
        )
    
    try:
        # Get expense item
        expense_item = db.query(ExpenseItem).filter(ExpenseItem.id == item_id).first()
        
        if not expense_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense item not found"
            )
        
        # Check organization access
        if current_user.role != UserRole.SUPER_ADMIN:
            if expense_item.expense.organization_id != current_user.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this expense item"
                )
        
        # Update expense item
        if "description" in item_data:
            expense_item.description = item_data["description"]
        if "amount" in item_data:
            expense_item.amount = item_data["amount"]
        if "category" in item_data:
            expense_item.category = item_data["category"]
        if "date" in item_data:
            expense_item.expense_date = datetime.strptime(item_data["date"], "%Y-%m-%d").date()
        if "receipt_number" in item_data:
            expense_item.receipt_number = item_data["receipt_number"]
        
        # Update related expense
        if "amount" in item_data:
            expense_item.expense.amount = item_data["amount"]
        if "category" in item_data:
            expense_item.expense.expense_type = ExpenseType(item_data["category"].upper())
        if "date" in item_data:
            expense_item.expense.expense_date = expense_item.expense_date
        
        db.commit()
        db.refresh(expense_item)
        
        return {
            "id": expense_item.id,
            "description": expense_item.description,
            "amount": float(expense_item.amount),
            "category": expense_item.category,
            "date": expense_item.expense_date.isoformat(),
            "receipt": expense_item.receipt_number,
            "status": expense_item.expense.status.value,
            "employee_name": f"{expense_item.expense.employee.first_name} {expense_item.expense.employee.last_name}",
            "expense_id": expense_item.expense_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating expense item: {str(e)}"
        )


@router.delete("/items/{item_id}")
async def delete_expense_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an expense item
    """
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete expense items"
        )
    
    try:
        # Get expense item
        expense_item = db.query(ExpenseItem).filter(ExpenseItem.id == item_id).first()
        
        if not expense_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense item not found"
            )
        
        # Check organization access
        if current_user.role != UserRole.SUPER_ADMIN:
            if expense_item.expense.organization_id != current_user.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to delete this expense item"
                )
        
        # Delete expense item and related expense
        expense_id = expense_item.expense_id
        db.delete(expense_item)
        
        # Check if there are other items for this expense
        remaining_items = db.query(ExpenseItem).filter(ExpenseItem.expense_id == expense_id).count()
        if remaining_items == 0:
            # Delete the expense if no other items
            expense = db.query(Expense).filter(Expense.id == expense_id).first()
            if expense:
                db.delete(expense)
        
        db.commit()
        
        return {"message": "Expense item deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting expense item: {str(e)}"
        )


@router.get("/reports")
async def get_expense_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None
):
    """
    Get expense reports with organization-specific filtering
    """
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view expense reports"
        )
    
    # Set organization filter
    if current_user.role == UserRole.SUPER_ADMIN:
        org_filter = True  # Super admin can see all data
    else:
        org_filter = ExpenseReport.organization_id == current_user.organization_id
    
    try:
        # Build query
        query = db.query(ExpenseReport).filter(org_filter)
        
        # Apply status filter (accept friendly alias "PENDING" for PENDING_APPROVAL)
        if status:
            status_value = status.upper()
            if status_value == "PENDING":
                status_value = "PENDING_APPROVAL"
            try:
                query = query.filter(ExpenseReport.status == ExpenseStatus(status_value))
            except Exception:
                # Ignore invalid status values to avoid server error
                pass
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        reports = query.offset(skip).limit(limit).all()
        
        # Format response
        expense_reports = []
        for report in reports:
            expense_reports.append({
                "id": report.id,
                "employee": f"{report.employee.first_name} {report.employee.last_name}",
                "title": report.title,
                "total_amount": float(report.total_amount),
                "status": report.status.value,
                "submitted_date": report.submitted_at.isoformat() if report.submitted_at else None,
                "approved_date": report.approved_at.isoformat() if report.approved_at else None,
                "items": len(report.expenses) if report.expenses else 0,
                "category": "Mixed"  # Could be calculated from expenses
            })
        
        return {
            "reports": expense_reports,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching expense reports: {str(e)}"
        )
