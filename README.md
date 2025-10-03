# HR Pilot - Multi-Organization Human Resources Management System

A comprehensive HR management system built with Python FastAPI, supporting multiple organizations with role-based access control.

## 🚀 Features

- **Multi-Organization Support**: Manage multiple companies/organizations
- **Role-Based Access Control**: 7 different user roles with specific permissions
- **Employee Management**: Complete employee lifecycle management
- **Attendance & Time Tracking**: Clock in/out, time tracking
- **Leave Management**: Request, approve, and track leave
- **Payroll System**: Salary management, payslips, reports
- **Document Management**: Secure file storage and sharing
- **Training & Development**: Course management and tracking
- **Expense Management**: Expense submission and approval
- **Reports & Analytics**: Comprehensive reporting system

## 👥 User Roles

1. **SUPER_ADMIN**: Full system access, cross-organization management
2. **ORG_ADMIN**: Organization-level admin
3. **HR**: HR operations and employee management
4. **MANAGER**: Team-level approvals
5. **DIRECTOR**: Department-level approvals
6. **PAYROLL**: Payroll management
7. **EMPLOYEE**: Self-service portal

## 🛠️ Tech Stack

- **Backend**: Python FastAPI
- **Database**: PostgreSQL with SQLAlchemy
- **Authentication**: JWT tokens
- **Frontend**: React with TypeScript
- **File Storage**: Local/Cloud storage
- **Email**: SMTP notifications

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Redis (for background tasks)
- Node.js 16+ (for frontend)

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd HRP
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your database and email settings
```

### 3. Database Setup
```bash
# Create PostgreSQL database
createdb hrpilot_db

# Run migrations
alembic upgrade head
```

### 4. Seed Default Data
```bash
python scripts/seed_data.py
```

### 5. Start the Application
```bash
# Backend
uvicorn app.main:app --reload

# Frontend (in separate terminal)
cd frontend
npm install
npm start
```

## 🔑 Default Accounts

All accounts use password: `Password123!`

- **SUPER_ADMIN**: superadmin@hrpilot.com
- **ORG_ADMIN**: orgadmin@hrpilot.com
- **HR**: hr@hrpilot.com
- **MANAGER**: manager@hrpilot.com
- **DIRECTOR**: director@hrpilot.com
- **PAYROLL**: payroll@hrpilot.com
- **EMPLOYEE**: employee@hrpilot.com

## 📁 Project Structure

```
HRP/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── organizations.py
│   │   │   ├── employees.py
│   │   │   ├── attendance.py
│   │   │   ├── leave.py
│   │   │   ├── payroll.py
│   │   │   └── reports.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── models/
│   │   ├── user.py
│   │   ├── organization.py
│   │   ├── employee.py
│   │   └── ...
│   ├── schemas/
│   │   ├── user.py
│   │   ├── organization.py
│   │   └── ...
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── email_service.py
│   │   └── ...
│   └── main.py
├── alembic/
├── scripts/
├── tests/
├── frontend/
└── uploads/
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py
```

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. 