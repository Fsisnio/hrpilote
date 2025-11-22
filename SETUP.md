# HR Pilot - Setup Guide

This guide will help you set up the HR Pilot multi-organization HR management system.

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **PostgreSQL 12+**
- **Redis** (optional, for background tasks)
- **Node.js 16+** (for frontend, optional)

### 1. Clone and Setup

```bash
# Clone the repository (if using git)
git clone <repository-url>
cd HRP

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Create PostgreSQL database
createdb hrpilot_db

# Or using psql:
psql -U postgres
CREATE DATABASE hrpilot_db;
\q
```

### 3. Environment Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env file with your settings
nano .env
```

**Required .env settings:**
```env
# Database (update with your credentials)
DATABASE_URL=postgresql://username:password@localhost:5432/hrpilot_db
# Optional: required when connecting to managed Postgres instances that force TLS
# For Render, set DATABASE_SSL_MODE=require
# DATABASE_SSL_MODE=require
# DATABASE_SSL_ROOT_CERT=/etc/ssl/certs/ca-certificates.crt

# MongoDB (in-progress migration)
MONGODB_URI=mongodb://localhost:27017/hrpilot
MONGODB_DB_NAME=hrpilot

# Security (generate secure keys)
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Email (optional for now)
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 4. Initialize Database

```bash
# Run the startup script to check setup
python start.py

# Seed default data
python scripts/seed_data.py
```

### 5. Start the Application

```bash
# Using the startup script
python start.py --server

# Or directly with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔑 Default Accounts

All accounts use password: `Jesus1993@`

| Role | Email | Description |
|------|-------|-------------|
| SUPER_ADMIN | superadmin@hrpilot.com | Full system access |
| ORG_ADMIN | orgadmin@hrpilot.com | Organization admin |
| HR | hr@hrpilot.com | HR operations |
| MANAGER | manager@hrpilot.com | Team manager |
| DIRECTOR | director@hrpilot.com | Department director |
| PAYROLL | payroll@hrpilot.com | Payroll specialist |
| EMPLOYEE | employee@hrpilot.com | Regular employee |

## 🏗️ Project Structure

```
HRP/
├── app/                    # Main application
│   ├── api/v1/            # API endpoints
│   │   ├── auth.py        # Authentication
│   │   ├── users.py       # User management
│   │   ├── organizations.py # Organization management
│   │   ├── employees.py   # Employee management
│   │   ├── attendance.py  # Attendance tracking
│   │   ├── leave.py       # Leave management
│   │   ├── payroll.py     # Payroll system
│   │   └── reports.py     # Reports and analytics
│   ├── core/              # Core functionality
│   │   ├── config.py      # Configuration
│   │   ├── database.py    # Database setup
│   │   └── security.py    # Security utilities
│   ├── models/            # Database models
│   │   ├── user.py        # User model
│   │   ├── organization.py # Organization model
│   │   ├── department.py  # Department model
│   │   └── employee.py    # Employee model
│   ├── schemas/           # Pydantic schemas
│   │   └── auth.py        # Authentication schemas
│   └── main.py            # FastAPI application
├── scripts/               # Utility scripts
│   └── seed_data.py       # Data seeding
├── tests/                 # Test files
├── uploads/               # File uploads
├── requirements.txt       # Python dependencies
├── start.py              # Startup script
└── README.md             # Project documentation
```

## 🔧 Configuration

### Database Configuration

The system uses PostgreSQL with SQLAlchemy ORM. Key settings:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/hrpilot_db
# DATABASE_SSL_MODE=require
# DATABASE_SSL_ROOT_CERT=/etc/ssl/certs/ca-certificates.crt
MONGODB_URI=mongodb://localhost:27017/hrpilot
MONGODB_DB_NAME=hrpilot
```

### Security Configuration

```env
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Password Policy

```env
MIN_PASSWORD_LENGTH=8
REQUIRE_UPPERCASE=true
REQUIRE_LOWERCASE=true
REQUIRE_NUMBERS=true
REQUIRE_SPECIAL_CHARS=true
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

## 🚀 Deployment

### Development

```bash
# Start with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
# Start production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker (Future)

```bash
# Build image
docker build -t hrpilot .

# Run container
docker run -p 8000:8000 hrpilot
```

## 🔍 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user profile

### Users
- `GET /api/v1/users/` - List users
- `GET /api/v1/users/{user_id}` - Get user details
- `PUT /api/v1/users/{user_id}/status` - Update user status

### Organizations
- `GET /api/v1/organizations/` - List organizations
- `GET /api/v1/organizations/{org_id}` - Get organization details

### Employees
- `GET /api/v1/employees/` - List employees
- `GET /api/v1/employees/{employee_id}` - Get employee details

### Attendance
- `POST /api/v1/attendance/clock-in` - Clock in
- `POST /api/v1/attendance/clock-out` - Clock out
- `GET /api/v1/attendance/records` - Get attendance records

### Leave Management
- `POST /api/v1/leave/request` - Request leave
- `GET /api/v1/leave/requests` - Get leave requests
- `PUT /api/v1/leave/{request_id}/approve` - Approve leave

### Payroll
- `GET /api/v1/payroll/payslips` - Get payslips
- `GET /api/v1/payroll/payslips/{payslip_id}` - Get payslip details
- `GET /api/v1/payroll/reports` - Get payroll reports

### Reports
- `GET /api/v1/reports/dashboard` - Dashboard data
- `GET /api/v1/reports/employee` - Employee reports
- `GET /api/v1/reports/attendance` - Attendance reports
- `GET /api/v1/reports/payroll` - Payroll reports

## 🛠️ Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check PostgreSQL is running
   - Verify database credentials in .env
   - Ensure database exists

2. **Import Errors**
   - Ensure virtual environment is activated
   - Check all dependencies are installed
   - Verify Python version is 3.9+

3. **Permission Errors**
   - Check file permissions
   - Ensure uploads directory exists
   - Verify database user permissions

### Logs

Check application logs for detailed error information:

```bash
# View logs
tail -f logs/app.log

# Check system logs
journalctl -u hrpilot -f
```

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Check logs for error details
4. Create an issue in the repository

## 🔄 Updates

To update the system:

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Run migrations (if any)
alembic upgrade head

# Restart the application
```

## 📝 License

This project is licensed under the MIT License. 