# Training Restrictions Implementation

## Overview
This implementation restricts employees to only enroll themselves in training courses, while preventing them from creating training courses or enrolling other employees. HR, Managers, and Admins retain full training management capabilities.

## Changes Made

### Backend Changes (app/api/v1/training.py)

#### 1. Modified `/enrollments` POST endpoint
- **File**: `app/api/v1/training.py`
- **Change**: Added role-based restriction to prevent employees from enrolling others
- **Code**: 
```python
# Check permissions - only HR, Managers, and Admins can enroll others
if current_user.role == UserRole.EMPLOYEE:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Employees can only enroll themselves. Use /enrollments/self-enroll endpoint."
    )
```

#### 2. Added `/enrollments/self-enroll` POST endpoint
- **Purpose**: Allows employees to enroll themselves in courses
- **Features**:
  - Validates course exists and is active
  - Finds employee record for current user
  - Prevents duplicate enrollments
  - Creates enrollment with proper status and notes

#### 3. Added `/enrollments/my-enrollments` GET endpoint
- **Purpose**: Returns enrollments for the current user (employee)
- **Features**:
  - Filters enrollments by current user's employee record
  - Returns only enrollments belonging to the logged-in employee

### Frontend Changes (frontend/src/pages/Training.tsx)

#### 1. Role-based UI restrictions
- **Create Course button**: Hidden for employees
- **Enroll Employee button**: Hidden for employees
- **Edit Course button**: Hidden for employees
- **Assessments tab**: Hidden for employees
- **Training Reports**: Hidden for employees

#### 2. Employee-specific features
- **Self-enroll button**: Added to course cards for employees
- **Enrollment status**: Shows "Already Enrolled" if employee is already enrolled
- **My Enrollments tab**: Shows only employee's own enrollments
- **Success notifications**: Shows alert when enrollment is successful

#### 3. Dynamic content
- **Header description**: Changes based on user role
- **Tab labels**: "My Enrollments" for employees vs "Enrollments" for others
- **Enrollment data**: Fetches different endpoints based on user role

### API Service Changes (frontend/src/services/api.ts)

#### Added new endpoints:
- `getMyEnrollments()`: Fetches current user's enrollments
- `selfEnroll(courseId)`: Enrolls current user in a course

## User Experience

### For Employees:
1. **Browse Courses**: Can view all available courses
2. **Self-Enroll**: Can enroll themselves in active courses
3. **View Progress**: Can see their own enrollment status and progress
4. **No Management**: Cannot create courses, enroll others, or manage assessments

### For HR/Managers/Admins:
1. **Full Management**: Can create, edit, and delete courses
2. **Enroll Others**: Can enroll any employee in courses
3. **View All**: Can see all enrollments across the organization
4. **Manage Assessments**: Can create and manage course assessments

## Security Features

1. **Backend Validation**: All restrictions are enforced at the API level
2. **Role-based Access**: Uses user roles to determine permissions
3. **Employee Record Validation**: Ensures employee record exists for current user
4. **Duplicate Prevention**: Prevents multiple enrollments in the same course

## Testing

A test script (`test_training_restrictions.py`) is provided to verify:
- Employees cannot create courses
- Employees cannot enroll others
- Employees can self-enroll
- Employees can view their enrollments
- HR can perform all training management tasks

## Usage Examples

### Employee Self-Enrollment
```javascript
// Frontend
await trainingAPI.selfEnroll(courseId);

// Backend
POST /api/v1/training/enrollments/self-enroll
{
  "course_id": 123
}
```

### Get Employee's Enrollments
```javascript
// Frontend
const myEnrollments = await trainingAPI.getMyEnrollments();

// Backend
GET /api/v1/training/enrollments/my-enrollments
```

### HR Enrolling Employee
```javascript
// Frontend
await trainingAPI.createEnrollment({
  course_id: 123,
  employee_id: 456
});

// Backend
POST /api/v1/training/enrollments
{
  "course_id": 123,
  "employee_id": 456
}
```

## Error Handling

The implementation includes proper error handling for:
- **403 Forbidden**: When employees try to perform restricted actions
- **404 Not Found**: When course or employee record doesn't exist
- **400 Bad Request**: When trying to enroll in already enrolled course
- **Frontend Feedback**: Success messages and error notifications

## Future Enhancements

Potential improvements could include:
1. **Bulk Enrollment**: Allow HR to enroll multiple employees at once
2. **Enrollment Approval**: Require manager approval for certain courses
3. **Prerequisites**: Check if employee meets course prerequisites
4. **Waitlist**: Handle courses that are at capacity
5. **Notifications**: Email notifications for enrollment confirmations
