from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, Enum, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from enum import Enum as PyEnum
from decimal import Decimal
from app.core.database import Base


class ExpenseType(PyEnum):
    TRAVEL = "TRAVEL"
    MEALS = "MEALS"
    ACCOMMODATION = "ACCOMMODATION"
    TRANSPORTATION = "TRANSPORTATION"
    OFFICE_SUPPLIES = "OFFICE_SUPPLIES"
    EQUIPMENT = "EQUIPMENT"
    SOFTWARE = "SOFTWARE"
    TRAINING = "TRAINING"
    ENTERTAINMENT = "ENTERTAINMENT"
    OTHER = "OTHER"


class ExpenseStatus(PyEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PaymentMethod(PyEnum):
    CASH = "CASH"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    BANK_TRANSFER = "BANK_TRANSFER"
    CHECK = "CHECK"
    COMPANY_CARD = "COMPANY_CARD"
    REIMBURSEMENT = "REIMBURSEMENT"


class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Expense details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    expense_type = Column(Enum(ExpenseType), nullable=False)
    category = Column(String(100), nullable=True)
    
    # Amount and currency
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD")
    exchange_rate = Column(Float, default=1.0)
    amount_usd = Column(Numeric(15, 2), default=0)
    
    # Date and location
    expense_date = Column(Date, nullable=False)
    location = Column(String(200), nullable=True)
    vendor = Column(String(200), nullable=True)
    
    # Payment details
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    receipt_number = Column(String(100), nullable=True)
    receipt_url = Column(String(500), nullable=True)
    
    # Status and approval
    status = Column(Enum(ExpenseStatus), default=ExpenseStatus.DRAFT)
    submitted_at = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Project and cost center
    project_id = Column(String(100), nullable=True)
    cost_center = Column(String(100), nullable=True)
    travel_request_id = Column(Integer, ForeignKey("travel_requests.id"), nullable=True)
    
    # Reimbursement
    is_reimbursable = Column(Boolean, default=True)
    reimbursement_amount = Column(Numeric(15, 2), default=0)
    reimbursed_at = Column(DateTime, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee", overlaps="expenses")
    organization = relationship("Organization")
    approver = relationship("User", foreign_keys=[approved_by])
    rejector = relationship("User", foreign_keys=[rejected_by])
    items = relationship("ExpenseItem", back_populates="expense", cascade="all, delete-orphan")


class ExpenseItem(Base):
    __tablename__ = "expense_items"
    
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)
    
    # Item details
    description = Column(String(200), nullable=False)
    expense_type = Column(Enum(ExpenseType), nullable=False)
    
    # Amount
    amount = Column(Numeric(15, 2), nullable=False)
    quantity = Column(Float, default=1.0)
    unit_price = Column(Numeric(15, 2), default=0)
    
    # Tax and discounts
    tax_amount = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    
    # Receipt
    receipt_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    expense = relationship("Expense", back_populates="items")


class ExpensePolicy(Base):
    __tablename__ = "expense_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Policy details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    expense_type = Column(Enum(ExpenseType), nullable=False)
    
    # Limits and rules
    daily_limit = Column(Numeric(15, 2), default=0)
    monthly_limit = Column(Numeric(15, 2), default=0)
    annual_limit = Column(Numeric(15, 2), default=0)
    
    # Approval thresholds
    requires_approval = Column(Boolean, default=True)
    approval_threshold = Column(Numeric(15, 2), default=0)
    approval_levels = Column(Integer, default=1)
    
    # Reimbursement rules
    reimbursement_percentage = Column(Float, default=100.0)
    requires_receipt = Column(Boolean, default=True)
    receipt_threshold = Column(Numeric(15, 2), default=0)
    
    # Restrictions
    allowed_vendors = Column(Text, nullable=True)  # JSON array
    restricted_vendors = Column(Text, nullable=True)  # JSON array
    allowed_locations = Column(Text, nullable=True)  # JSON array
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")


class ExpenseReport(Base):
    __tablename__ = "expense_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Report details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    report_number = Column(String(50), nullable=True)
    
    # Period
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Totals
    total_amount = Column(Numeric(15, 2), default=0)
    total_reimbursable = Column(Numeric(15, 2), default=0)
    total_approved = Column(Numeric(15, 2), default=0)
    total_paid = Column(Numeric(15, 2), default=0)
    
    # Status and approval
    status = Column(Enum(ExpenseStatus), default=ExpenseStatus.DRAFT)
    submitted_at = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee", overlaps="expense_reports")
    organization = relationship("Organization")
    approver = relationship("User", foreign_keys=[approved_by])
    expenses = relationship("Expense", secondary="expense_report_items")


class ExpenseReportItem(Base):
    __tablename__ = "expense_report_items"
    
    id = Column(Integer, primary_key=True, index=True)
    expense_report_id = Column(Integer, ForeignKey("expense_reports.id"), nullable=False)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    expense_report = relationship("ExpenseReport", overlaps="expenses")
    expense = relationship("Expense", overlaps="expenses")


class TravelRequest(Base):
    __tablename__ = "travel_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Travel details
    purpose = Column(String(200), nullable=False)
    destination = Column(String(200), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Travel type
    travel_type = Column(String(50), nullable=False)  # BUSINESS, CONFERENCE, TRAINING, etc.
    is_international = Column(Boolean, default=False)
    
    # Estimated costs
    estimated_cost = Column(Numeric(15, 2), default=0)
    budget_approved = Column(Numeric(15, 2), default=0)
    
    # Status and approval
    status = Column(String(20), default="PENDING")  # PENDING, APPROVED, REJECTED, CANCELLED
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee", overlaps="travel_requests")
    organization = relationship("Organization")
    approver = relationship("User", foreign_keys=[approved_by])
    expenses = relationship("Expense", foreign_keys="Expense.travel_request_id")


class AdvanceRequest(Base):
    __tablename__ = "advance_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Advance details
    purpose = Column(String(200), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD")
    
    # Expected expenses
    expected_expense_date = Column(Date, nullable=True)
    expected_expense_description = Column(Text, nullable=True)
    
    # Status and approval
    status = Column(String(20), default="PENDING")  # PENDING, APPROVED, REJECTED, PAID, SETTLED
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    settled_at = Column(DateTime, nullable=True)
    
    # Settlement
    settled_amount = Column(Numeric(15, 2), default=0)
    refund_amount = Column(Numeric(15, 2), default=0)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee", overlaps="advance_requests")
    organization = relationship("Organization")
    approver = relationship("User", foreign_keys=[approved_by]) 