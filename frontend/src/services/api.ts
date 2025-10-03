import axios from 'axios';

const API_BASE_URL = 'http://localhost:3003/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, try to refresh
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem('access_token', response.data.access_token);
          localStorage.setItem('refresh_token', response.data.refresh_token);
          
          // Retry original request
          error.config.headers.Authorization = `Bearer ${response.data.access_token}`;
          return api.request(error.config);
        } catch (refreshError) {
          // Refresh failed, try no-auth logout and redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          try {
            await authAPI.logoutNoAuth();
          } catch (logoutError) {
            console.error('Logout failed:', logoutError);
          }
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  
  logout: () => api.post('/auth/logout'),
  
  logoutNoAuth: () => api.post('/auth/logout-no-auth'),
  
  getCurrentUser: () => api.get('/auth/me'),
  
  changePassword: (currentPassword: string, newPassword: string, confirmPassword: string) =>
    api.post('/auth/change-password', { 
      current_password: currentPassword, 
      new_password: newPassword, 
      confirm_password: confirmPassword 
    }),
};

// Users API
export const usersAPI = {
  getUsers: (params?: any) => api.get('/users', { params }),
  getUser: (id: number) => api.get(`/users/${id}`),
  createUser: (data: any) => api.post('/users', data),
  updateUser: (id: number, data: any) => api.put(`/users/${id}`, data),
  updateUserStatus: (id: number, status: string) =>
    api.put(`/users/${id}/status`, { status }),
  deleteUser: (id: number) => api.delete(`/users/${id}`),
};

// Organizations API
export const organizationsAPI = {
  getOrganizations: () => api.get('/organizations/'),
  getOrganization: (id: number) => api.get(`/organizations/${id}`),
  createOrganization: (data: any) => api.post('/organizations/', data),
  updateOrganization: (id: number, data: any) => api.put(`/organizations/${id}`, data),
  deleteOrganization: (id: number) => api.delete(`/organizations/${id}`),
};

// Employees API
export const employeesAPI = {
  getEmployees: (params?: any) => api.get('/employees', { params }),
  getEmployee: (id: number) => api.get(`/employees/${id}`),
  createEmployee: (data: any) => api.post('/employees', data),
  updateEmployee: (id: number, data: any) => api.put(`/employees/${id}`, data),
  updateEmployeeStatus: (id: number, status: string) =>
    api.put(`/employees/${id}/status`, { new_status: status }),
  deleteEmployee: (id: number) => api.delete(`/employees/${id}`),
  getUsersWithoutEmployeeRecord: () => api.get('/employees/users-without-employee-record'),
};

// Documents API
export const documentsAPI = {
  getDocuments: (params?: any) => api.get('/documents', { params }),
  getDocument: (id: number) => api.get(`/documents/${id}`),
  uploadDocument: (formData: FormData) => api.post('/documents', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  updateDocument: (id: number, data: any) => api.put(`/documents/${id}`, data),
  deleteDocument: (id: number) => api.delete(`/documents/${id}`),
  downloadDocument: (id: number) => api.get(`/documents/${id}/download`, {
    responseType: 'blob',
  }),
};

// Training API
export const trainingAPI = {
  // Courses
  getCourses: (params?: any) => api.get('/training/courses', { params }),
  getCourse: (id: number) => api.get(`/training/courses/${id}`),
  createCourse: (data: any) => api.post('/training/courses', data),
  updateCourse: (id: number, data: any) => api.put(`/training/courses/${id}`, data),
  deleteCourse: (id: number) => api.delete(`/training/courses/${id}`),
  
  // Enrollments
  getEnrollments: (params?: any) => api.get('/training/enrollments', { params }),
  getMyEnrollments: () => api.get('/training/enrollments/my-enrollments'),
  createEnrollment: (data: any) => api.post('/training/enrollments', data),
  selfEnroll: (courseId: number) => api.post('/training/enrollments/self-enroll', { course_id: courseId }),
  updateEnrollment: (id: number, data: any) => api.put(`/training/enrollments/${id}`, data),
  
  // Assessments
  getAssessments: (params?: any) => api.get('/training/assessments', { params }),
  getAssessment: (id: number) => api.get(`/training/assessments/${id}`),
  createAssessment: (data: any) => api.post('/training/assessments', data),
  updateAssessment: (id: number, data: any) => api.put(`/training/assessments/${id}`, data),
  deleteAssessment: (id: number) => api.delete(`/training/assessments/${id}`),
  
  // Assessment Results
  getAssessmentResults: (params?: any) => api.get('/training/assessment-results', { params }),
  createAssessmentResult: (data: any) => api.post('/training/assessment-results', data),
  updateAssessmentResult: (id: number, data: any) => api.put(`/training/assessment-results/${id}`, data),
  
  // Skills
  getSkills: (params?: any) => api.get('/training/skills', { params }),
  createSkill: (data: any) => api.post('/training/skills', data),
  
  // Employee Skills
  getEmployeeSkills: (params?: any) => api.get('/training/employee-skills', { params }),
  createEmployeeSkill: (data: any) => api.post('/training/employee-skills', data),
  
  // Training Sessions
  getTrainingSessions: (params?: any) => api.get('/training/sessions', { params }),
  createTrainingSession: (data: any) => api.post('/training/sessions', data),
  
  // Statistics
  getTrainingSummary: () => api.get('/training/summary'),
  getCourseStatistics: (courseId: number) => api.get(`/training/courses/${courseId}/statistics`),
};

// Leave API
export const leaveAPI = {
  // Leave Requests
  getLeaveRequests: (params?: any) => api.get('/leave/requests', { params }),
  getLeaveRequest: (id: number) => api.get(`/leave/requests/${id}`),
  createLeaveRequest: (data: any) => api.post('/leave/requests', data),
  updateLeaveRequest: (id: number, data: any) => api.put(`/leave/requests/${id}`, data),
  deleteLeaveRequest: (id: number) => api.delete(`/leave/requests/${id}`),
  approveLeaveRequest: (id: number) => api.put(`/leave/requests/${id}/approve`),
  rejectLeaveRequest: (id: number, reason: string) => api.put(`/leave/requests/${id}/reject`, { reason }),
  
  // Leave Balances
  getLeaveBalances: (employeeId?: number) => api.get('/leave/balances', { params: { employee_id: employeeId } }),
  getLeaveBalancesSummary: () => api.get('/leave/balances/summary'),
  
  // Leave Policies
  getLeavePolicies: () => api.get('/leave/policies'),
};

// Attendance API
export const attendanceAPI = {
  // Clock In/Out
  clockIn: (data: any) => api.post('/attendance/clock-in', data),
  clockOut: (data: any) => api.post('/attendance/clock-out', data),
  
  // Breaks
  startBreak: (data: any) => api.post('/attendance/break/start', data),
  endBreak: () => api.post('/attendance/break/end'),
  
  // Attendance Records
  getTodayAttendance: () => api.get('/attendance/today'),
  getAttendanceHistory: (startDate: string, endDate: string) => 
    api.get('/attendance/history', { params: { start_date: startDate, end_date: endDate } }),
  getAttendanceSummary: (month: number, year: number) => 
    api.get('/attendance/summary', { params: { month, year } }),
  
  // Work Schedules
  getWorkSchedules: (params?: any) => api.get('/attendance/schedules', { params }),
  createWorkSchedule: (data: any) => api.post('/attendance/schedules', data),
  
  // Time Off Requests
  getTimeOffRequests: (params?: any) => api.get('/attendance/time-off', { params }),
  createTimeOffRequest: (data: any) => api.post('/attendance/time-off', data),
};

// Payroll API
export const payrollAPI = {
  // Summary and Statistics
  getPayrollSummary: () => api.get('/payroll/summary'),
  
  // Payroll Records
  getPayrollRecords: (params?: any) => api.get('/payroll/records', { params }),
  createPayrollRecord: (data: any) => api.post('/payroll/records', data),
  updatePayrollRecord: (recordId: number, data: any) => api.put(`/payroll/records/${recordId}`, data),
  
  // Recent Activity
  getPayrollActivity: (limit?: number) => api.get('/payroll/activity', { params: { limit } }),
  
  // Departments for filtering
  getDepartments: () => api.get('/payroll/departments'),
  
  // Process Payroll
  processPayroll: () => api.post('/payroll/process'),
  
  // Generate Reports
  generateReport: (reportType: string, month?: number, year?: number) => 
    api.post('/payroll/generate-report', null, { 
      params: { 
        report_type: reportType, 
        month, 
        year 
      } 
    }),
  
  // Download PDF Reports
  downloadPDF: (reportType: string, month?: number, year?: number) => 
    api.get('/payroll/download-pdf', { 
      params: { 
        report_type: reportType, 
        month, 
        year 
      },
      responseType: 'blob'
    }),
  
  // Reports (placeholder)
  getPayrollReports: () => api.get('/payroll/reports'),
  
  // Payslips (placeholder)
  getPayslips: () => api.get('/payroll/payslips'),
  getPayslip: (id: number) => api.get(`/payroll/payslips/${id}`),
  
  // Settings
  getPayrollSettings: () => api.get('/payroll/settings'),
  updatePayrollSettings: (data: any) => api.put('/payroll/settings', data),
};

// Reports API
export const reportsAPI = {
  // Dashboard data
  getDashboardData: () => api.get('/reports/dashboard'),
  
  // Employee reports
  getEmployeeReports: (startDate?: string, endDate?: string) => 
    api.get('/reports/employee', { 
      params: { start_date: startDate, end_date: endDate } 
    }),
  
  // Attendance reports
  getAttendanceReports: (startDate?: string, endDate?: string) => 
    api.get('/reports/attendance', { 
      params: { start_date: startDate, end_date: endDate } 
    }),
  
  // Payroll reports
  getPayrollReports: (month?: number, year?: number) => 
    api.get('/reports/payroll', { 
      params: { month, year } 
    }),
};

// Expenses API
export const expensesAPI = {
  // Expense Items
  getExpenseItems: (params?: any) => api.get('/expenses/items', { params }),
  createExpenseItem: (data: any) => api.post('/expenses/items', data),
  updateExpenseItem: (id: number, data: any) => api.put(`/expenses/items/${id}`, data),
  deleteExpenseItem: (id: number) => api.delete(`/expenses/items/${id}`),
  
  // Expense Reports
  getExpenseReports: (params?: any) => api.get('/expenses/reports', { params }),
};

export default api; 