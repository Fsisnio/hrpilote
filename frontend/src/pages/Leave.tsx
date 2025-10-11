import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import Modal from '../components/Modal';
import Toast from '../components/Toast';
import { leaveAPI, employeesAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { UserRole } from '../types';

const Leave: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('requests');
  const [isNewLeaveModalOpen, setIsNewLeaveModalOpen] = useState(false);
  const [isViewLeaveModalOpen, setIsViewLeaveModalOpen] = useState(false);
  const [selectedLeaveRequest, setSelectedLeaveRequest] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [leaveRequests, setLeaveRequests] = useState<any[]>([]);
  const [leaveBalances, setLeaveBalances] = useState<any[]>([]);
  const [employees, setEmployees] = useState<any[]>([]);
  const [currentEmployee, setCurrentEmployee] = useState<any>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info'; isVisible: boolean }>({
    message: '',
    type: 'info',
    isVisible: false
  });
  const [newLeaveRequest, setNewLeaveRequest] = useState({
    employee_id: '',
    leave_type: 'ANNUAL',
    start_date: '',
    end_date: '',
    reason: '',
    notes: ''
  });

  // Calculate dynamic metrics from leave requests
  const calculateMetrics = () => {
    const currentMonth = new Date().getMonth();
    const currentYear = new Date().getFullYear();
    
    // Filter requests for current month
    const currentMonthRequests = leaveRequests.filter(request => {
      const requestDate = new Date(request.created_at || request.start_date);
      return requestDate.getMonth() === currentMonth && requestDate.getFullYear() === currentYear;
    });

    const pendingRequests = leaveRequests.filter(request => request.status === 'PENDING').length;
    const approvedThisMonth = currentMonthRequests.filter(request => request.status === 'APPROVED').length;
    const rejectedThisMonth = currentMonthRequests.filter(request => request.status === 'REJECTED').length;
    
    // Calculate average processing time for approved/rejected requests
    const processedRequests = leaveRequests.filter(request => 
      request.status === 'APPROVED' || request.status === 'REJECTED'
    );
    
    let averageProcessingTime = 0;
    if (processedRequests.length > 0) {
      const totalProcessingTime = processedRequests.reduce((total, request) => {
        const createdDate = new Date(request.created_at || request.start_date);
        const processedDate = new Date(request.updated_at || request.end_date);
        const processingDays = Math.ceil((processedDate.getTime() - createdDate.getTime()) / (1000 * 60 * 60 * 24));
        return total + Math.max(0, processingDays);
      }, 0);
      averageProcessingTime = totalProcessingTime / processedRequests.length;
    }

    return {
      pendingRequests,
      approvedThisMonth,
      rejectedThisMonth,
      averageProcessingTime: averageProcessingTime.toFixed(1)
    };
  };

  const metrics = calculateMetrics();

  // Check if current user is an employee
  const isEmployee = user?.role === UserRole.EMPLOYEE;
  
  // Debug logging
  console.log('Current user:', user);
  console.log('Is employee:', isEmployee);
  console.log('Current employee:', currentEmployee);

  // Fetch data on component mount
  useEffect(() => {
    console.log('Leave component mounted, fetching data...');
    console.log('Current user from localStorage:', localStorage.getItem('access_token') ? 'Token exists' : 'No token');
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch leave requests
      console.log('Fetching leave requests...');
      try {
        const requestsResponse = await leaveAPI.getLeaveRequests();
        console.log('Leave requests response:', requestsResponse);
        console.log('Leave requests response data:', requestsResponse.data);
        console.log('Leave requests response status:', requestsResponse.status);
        setLeaveRequests(requestsResponse.data || []);
        console.log('Leave requests data set:', requestsResponse.data || []);
      } catch (err: any) {
        console.error('Error fetching leave requests:', err);
        console.error('Error response:', err.response);
        console.error('Error status:', err.response?.status);
        console.error('Error data:', err.response?.data);
        throw new Error(`Failed to fetch leave requests: ${err.response?.data?.detail || err.message}`);
      }
      
      // Fetch employees for the form (only for non-employee users)
      if (!isEmployee) {
        console.log('Fetching employees...');
        try {
          const employeesResponse = await employeesAPI.getEmployees();
          console.log('Employees response:', employeesResponse);
          setEmployees(employeesResponse.data);
        } catch (err: any) {
          console.error('Error fetching employees:', err);
          // Don't throw here, as this is not critical for the main functionality
          setEmployees([]);
        }
      } else {
        // For employees, get their own employee record
        console.log('Fetching current employee data...');
        try {
          const employeesResponse = await employeesAPI.getEmployees();
          const currentEmp = employeesResponse.data.find((emp: any) => emp.user_id === user?.id);
          if (currentEmp) {
            setCurrentEmployee(currentEmp);
            setNewLeaveRequest(prev => ({ ...prev, employee_id: currentEmp.id.toString() }));
          }
        } catch (err: any) {
          console.error('Error fetching current employee data:', err);
        }
      }
      
      // Fetch leave balances summary for the organization
      console.log('Fetching leave balances...');
      try {
        const balancesResponse = await leaveAPI.getLeaveBalancesSummary();
        console.log('Leave balances response:', balancesResponse);
        console.log('Leave balances response data:', balancesResponse.data);
        console.log('Leave balances response status:', balancesResponse.status);
        setLeaveBalances(balancesResponse.data || []);
      } catch (err: any) {
        console.error('Error fetching leave balances:', err);
        console.error('Error response:', err.response);
        console.error('Error status:', err.response?.status);
        console.error('Error data:', err.response?.data);
        // Check if it's an employee profile not found error
        if (err.response?.data?.detail && err.response.data.detail.includes('Employee profile not found')) {
          throw new Error('Please, use your employee profile');
        }
        throw new Error(`Failed to fetch leave balances: ${err.response?.data?.detail || err.message}`);
      }
      
    } catch (err: any) {
      console.error('Error fetching leave data:', err);
      let errorMessage = 'Failed to fetch leave data';
      
      if (err.message) {
        errorMessage = err.message;
      } else if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          errorMessage = err.response.data.detail.map((error: any) => error.msg || 'Validation error').join(', ');
        } else {
          errorMessage = 'An error occurred while fetching data';
        }
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Approved': return 'bg-green-100 text-green-800';
      case 'Pending': return 'bg-yellow-100 text-yellow-800';
      case 'Rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'Annual': return 'bg-blue-100 text-blue-800';
      case 'Sick': return 'bg-red-100 text-red-800';
      case 'Personal': return 'bg-purple-100 text-purple-800';
      case 'Maternity': return 'bg-pink-100 text-pink-800';
      case 'Paternity': return 'bg-indigo-100 text-indigo-800';
      case 'Bereavement': return 'bg-gray-100 text-gray-800';
      case 'Unpaid': return 'bg-yellow-100 text-yellow-800';
      case 'Compensatory': return 'bg-green-100 text-green-800';
      case 'Study': return 'bg-cyan-100 text-cyan-800';
      case 'Other': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const showToast = (message: string, type: 'success' | 'error' | 'info') => {
    setToast({ message, type, isVisible: true });
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setNewLeaveRequest(prev => ({ ...prev, [name]: value }));
  };

  const handleOpenNewLeaveModal = () => {
    // Reset form and set employee_id for employees
    setNewLeaveRequest({
      employee_id: isEmployee && currentEmployee ? currentEmployee.id.toString() : '',
      leave_type: 'ANNUAL',
      start_date: '',
      end_date: '',
      reason: '',
      notes: ''
    });
    setIsNewLeaveModalOpen(true);
  };

  const handleViewLeaveRequest = (request: any) => {
    setSelectedLeaveRequest(request);
    setIsViewLeaveModalOpen(true);
    
    // Debug logging for authorization
    console.log('Viewing leave request:', request);
    console.log('Current user role:', user?.role);
    console.log('Can approve/reject:', user && [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR].includes(user.role));
  };

  const handleApproveLeaveRequest = async (requestId: number) => {
    try {
      await leaveAPI.approveLeaveRequest(requestId);
      showToast('Leave request approved successfully!', 'success');
      fetchData();
      setIsViewLeaveModalOpen(false);
    } catch (error: any) {
      console.error('Failed to approve leave request:', error);
      showToast('Failed to approve leave request', 'error');
    }
  };

  const handleRejectLeaveRequest = async (requestId: number) => {
    try {
      await leaveAPI.rejectLeaveRequest(requestId, 'Rejected by manager');
      showToast('Leave request rejected successfully!', 'success');
      fetchData();
      setIsViewLeaveModalOpen(false);
    } catch (error: any) {
      console.error('Failed to reject leave request:', error);
      showToast('Failed to reject leave request', 'error');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB');
  };

  const calculateDays = (startDate: string, endDate: string) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end.getTime() - start.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
    return diffDays;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      // For employees, ensure the employee_id is set to their own ID
      const employeeId = isEmployee && currentEmployee ? currentEmployee.id : (newLeaveRequest.employee_id ? parseInt(newLeaveRequest.employee_id) : null);
      
      // Validate employee_id is present
      if (!employeeId) {
        showToast('Employee ID is required', 'error');
        setIsSubmitting(false);
        return;
      }
      
      console.log('Creating leave request with data:', newLeaveRequest);
      console.log('Employee ID being sent:', employeeId);
      console.log('Is employee:', isEmployee);
      console.log('Current employee:', currentEmployee);
      const response = await leaveAPI.createLeaveRequest({
        ...newLeaveRequest,
        employee_id: employeeId,
        start_date: newLeaveRequest.start_date,
        end_date: newLeaveRequest.end_date
      });
      console.log('Leave request created successfully:', response);
      
      setIsNewLeaveModalOpen(false);
      setNewLeaveRequest({
        employee_id: isEmployee && currentEmployee ? currentEmployee.id.toString() : '',
        leave_type: 'ANNUAL',
        start_date: '',
        end_date: '',
        reason: '',
        notes: ''
      });
      
      // Refresh the data
      console.log('Refreshing data after creation...');
      fetchData();
      showToast('Leave request created successfully!', 'success');
    } catch (error: any) {
      console.error('Failed to create leave request:', error);
      let errorMessage = 'Failed to create leave request';
      
      if (error.response?.data?.detail) {
        // Handle both string and object error details
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map((err: any) => err.msg || 'Validation error').join(', ');
        } else {
          errorMessage = 'Validation error occurred';
        }
      }
      
      showToast(errorMessage, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <div className="text-xl">Loading leave data...</div>
          </div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="text-center py-12">
          <div className="text-red-600 text-6xl mb-4">⚠️</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Leave Data</h3>
          <p className="text-gray-600 mb-4">{typeof error === 'string' ? error : 'An error occurred while loading data'}</p>
          <div className="space-x-2">
            <button 
              onClick={fetchData}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md"
            >
              Retry
            </button>
            <button 
              onClick={() => setError(null)}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md"
            >
              Dismiss
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Leave Management</h1>
            <p className="text-gray-600">Manage leave requests and balances</p>
          </div>
          <button 
            onClick={handleOpenNewLeaveModal}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md"
          >
            New Leave Request
          </button>
        </div>

        {/* Leave Balance Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {leaveBalances.length > 0 ? (
            leaveBalances.map((balance) => (
              <div key={balance.type} className="bg-white p-4 rounded-lg shadow">
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900 mb-2">{balance.type}</div>
                  <div className="text-3xl font-bold text-indigo-600 mb-2">{balance.remaining}</div>
                  <div className="text-sm text-gray-600">
                    {balance.used} used of {balance.total}
                  </div>
                  <div className="mt-2">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-indigo-600 h-2 rounded-full" 
                        style={{ width: `${(balance.used / balance.total) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-5 text-center py-8">
              <div className="text-gray-400 text-4xl mb-2">📊</div>
              <p className="text-gray-600">No leave balance data available</p>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              <button
                onClick={() => setActiveTab('requests')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'requests'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Leave Requests
              </button>
              <button
                onClick={() => setActiveTab('calendar')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'calendar'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Calendar View
              </button>
              <button
                onClick={() => setActiveTab('policies')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'policies'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Leave Policies
              </button>
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'requests' && (
              <div>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Leave Requests</h3>
                  <div className="flex space-x-2">
                    <select className="border border-gray-300 rounded-md px-3 py-1 text-sm">
                      <option>All Statuses</option>
                      <option>Pending</option>
                      <option>Approved</option>
                      <option>Rejected</option>
                    </select>
                    <select className="border border-gray-300 rounded-md px-3 py-1 text-sm">
                      <option>All Types</option>
                      <option>Vacation</option>
                      <option>Sick Leave</option>
                      <option>Personal</option>
                    </select>
                  </div>
                </div>

                {leaveRequests.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Employee
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Type
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Dates
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Days
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Status
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {leaveRequests.map((request) => (
                        <tr key={request.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">{request.employee_name}</div>
                            <div className="text-sm text-gray-500">{request.reason}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getTypeColor(request.leave_type)}`}>
                              {request.leave_type.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <div>{new Date(request.start_date).toLocaleDateString()}</div>
                            <div className="text-gray-500">to {new Date(request.end_date).toLocaleDateString()}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {request.total_days} days
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(request.status)}`}>
                              {request.status.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              {request.status === 'Pending' && (
                                <>
                                  <button 
                                    onClick={() => handleApproveLeaveRequest(request.id)}
                                    className="text-green-600 hover:text-green-900"
                                  >
                                    Approve
                                  </button>
                                  <button 
                                    onClick={() => handleRejectLeaveRequest(request.id)}
                                    className="text-red-600 hover:text-red-900"
                                  >
                                    Reject
                                  </button>
                                </>
                              )}
                              <button 
                                onClick={() => handleViewLeaveRequest(request)}
                                className="text-indigo-600 hover:text-indigo-900"
                              >
                                View
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-gray-400 text-6xl mb-4">📋</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Leave Requests</h3>
                  <p className="text-gray-600 mb-4">No leave requests have been submitted yet.</p>
                  <button 
                    onClick={handleOpenNewLeaveModal}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md"
                  >
                    Create First Request
                  </button>
                </div>
              )}
              </div>
            )}

            {activeTab === 'calendar' && (
              <div className="text-center py-12">
                <div className="text-gray-400 text-6xl mb-4">📅</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Calendar View</h3>
                <p className="text-gray-600">Calendar view will be implemented here</p>
              </div>
            )}

            {activeTab === 'policies' && (
              <div className="space-y-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">Vacation Leave Policy</h4>
                  <p className="text-sm text-gray-600">
                    Employees are entitled to 20 days of vacation leave per year. Leave requests must be submitted at least 2 weeks in advance.
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">Sick Leave Policy</h4>
                  <p className="text-sm text-gray-600">
                    Employees are entitled to 10 days of sick leave per year. Medical certificates may be required for extended absences.
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">Personal Leave Policy</h4>
                  <p className="text-sm text-gray-600">
                    Employees are entitled to 5 days of personal leave per year for personal matters.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Quick Stats - Only show for non-employee roles */}
        {!isEmployee && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <span className="text-yellow-600 text-xl">⏳</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Pending Requests</p>
                  <p className="text-2xl font-semibold text-gray-900">{metrics.pendingRequests}</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <span className="text-green-600 text-xl">✅</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Approved This Month</p>
                  <p className="text-2xl font-semibold text-gray-900">{metrics.approvedThisMonth}</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 bg-red-100 rounded-lg">
                  <span className="text-red-600 text-xl">❌</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Rejected This Month</p>
                  <p className="text-2xl font-semibold text-gray-900">{metrics.rejectedThisMonth}</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <span className="text-blue-600 text-xl">📊</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Average Processing Time</p>
                  <p className="text-2xl font-semibold text-gray-900">{metrics.averageProcessingTime} days</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* New Leave Request Modal */}
      <Modal
        isOpen={isNewLeaveModalOpen}
        onClose={() => setIsNewLeaveModalOpen(false)}
        title="New Leave Request"
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Employee *
              </label>
              {isEmployee ? (
                // For employees, show their name as read-only
                <div className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-900">
                  {currentEmployee ? `${currentEmployee.first_name} ${currentEmployee.last_name}` : `${user?.first_name} ${user?.last_name}`}
                  {/* Debug info */}
                  <div className="text-xs text-gray-500 mt-1">
                    Employee ID: {currentEmployee?.id || 'Not set'}
                  </div>
                </div>
              ) : (
                // For other users, show dropdown
                <select
                  name="employee_id"
                  value={newLeaveRequest.employee_id}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select Employee</option>
                  {employees.map(employee => (
                    <option key={employee.id} value={employee.id}>
                      {employee.first_name} {employee.last_name} ({employee.employee_id})
                    </option>
                  ))}
                </select>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Leave Type *
              </label>
              <select
                name="leave_type"
                value={newLeaveRequest.leave_type}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="ANNUAL">Annual Leave</option>
                <option value="SICK">Sick Leave</option>
                <option value="PERSONAL">Personal Leave</option>
                <option value="MATERNITY">Maternity Leave</option>
                <option value="PATERNITY">Paternity Leave</option>
                <option value="BEREAVEMENT">Bereavement Leave</option>
                <option value="UNPAID">Unpaid Leave</option>
                <option value="COMPENSATORY">Compensatory Leave</option>
                <option value="STUDY">Study Leave</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Date *
              </label>
              <input
                type="date"
                name="start_date"
                value={newLeaveRequest.start_date}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Date *
              </label>
              <input
                type="date"
                name="end_date"
                value={newLeaveRequest.end_date}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reason *
            </label>
            <input
              type="text"
              name="reason"
              value={newLeaveRequest.reason}
              onChange={handleInputChange}
              required
              placeholder="Brief reason for leave"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                Notes
              </label>
              <textarea
                name="notes"
                value={newLeaveRequest.notes}
              onChange={handleInputChange}
              rows={3}
              placeholder="Additional details about the leave request"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={() => setIsNewLeaveModalOpen(false)}
              className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Creating...' : 'Create Leave Request'}
            </button>
          </div>
        </form>
      </Modal>

      {/* View Leave Request Modal */}
      <Modal
        isOpen={isViewLeaveModalOpen}
        onClose={() => setIsViewLeaveModalOpen(false)}
        title="Leave Request Details"
        size="lg"
      >
        {selectedLeaveRequest && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Employee
                </label>
                <p className="text-sm text-gray-900">
                  {selectedLeaveRequest.employee?.first_name} {selectedLeaveRequest.employee?.last_name}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Leave Type
                </label>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getTypeColor(selectedLeaveRequest.leave_type)}`}>
                  {selectedLeaveRequest.leave_type.replace('_', ' ')}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date
                </label>
                <p className="text-sm text-gray-900">
                  {formatDate(selectedLeaveRequest.start_date)}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  End Date
                </label>
                <p className="text-sm text-gray-900">
                  {formatDate(selectedLeaveRequest.end_date)}
                </p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Duration
              </label>
              <p className="text-sm text-gray-900">
                {calculateDays(selectedLeaveRequest.start_date, selectedLeaveRequest.end_date)} days
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Reason
              </label>
              <p className="text-sm text-gray-900">
                {selectedLeaveRequest.reason || 'No reason provided'}
              </p>
            </div>

            {selectedLeaveRequest.notes && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes
                </label>
                <p className="text-sm text-gray-900">
                  {selectedLeaveRequest.notes}
                </p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(selectedLeaveRequest.status)}`}>
                {selectedLeaveRequest.status.replace('_', ' ')}
              </span>
            </div>

            {selectedLeaveRequest.status === 'PENDING' && user && [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR].includes(user.role) && (
              <div className="flex justify-end space-x-3 pt-4 border-t">
                <button
                  onClick={() => handleRejectLeaveRequest(selectedLeaveRequest.id)}
                  className="px-4 py-2 text-red-700 bg-red-100 rounded-md hover:bg-red-200"
                >
                  Reject
                </button>
                <button
                  onClick={() => handleApproveLeaveRequest(selectedLeaveRequest.id)}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  Approve
                </button>
              </div>
            )}
            
            {selectedLeaveRequest.status === 'PENDING' && user && user.role === UserRole.EMPLOYEE && (
              <div className="pt-4 border-t">
                <p className="text-sm text-gray-600 text-center">
                  Your leave request is pending approval. Please contact your manager or HR department for updates.
                </p>
              </div>
            )}
            
            {selectedLeaveRequest.status === 'PENDING' && user && ![UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR].includes(user.role) && user.role !== UserRole.EMPLOYEE && (
              <div className="pt-4 border-t">
                <p className="text-sm text-gray-600 text-center">
                  You don't have permission to approve or reject leave requests.
                </p>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Toast Notification */}
      <Toast
        message={toast.message}
        type={toast.type}
        isVisible={toast.isVisible}
        onClose={() => setToast(prev => ({ ...prev, isVisible: false }))}
      />
    </Layout>
  );
};

export default Leave; 