import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { employeesAPI, leaveAPI } from '../../services/api';
import { Employee } from '../../types';
import Layout from '../Layout';
import { useNavigate } from 'react-router-dom';

const OrgAdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    pendingRequests: 0,
    approvedThisMonth: 0,
    rejectedThisMonth: 0,
    averageProcessingTime: 2.3
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch employees
        const employeesRes = await employeesAPI.getEmployees();
        setEmployees(Array.isArray(employeesRes.data) ? employeesRes.data : []);

        // Fetch leave requests for admin stats
        try {
          const leaveRes = await leaveAPI.getLeaveRequests();
          const leaveRequests = Array.isArray(leaveRes.data) ? leaveRes.data : [];
          
          // Calculate stats
          const currentMonth = new Date().getMonth();
          const currentYear = new Date().getFullYear();
          
          const pendingRequests = leaveRequests.filter(req => req.status === 'PENDING').length;
          const approvedThisMonth = leaveRequests.filter(req => 
            req.status === 'APPROVED' && 
            new Date(req.created_at).getMonth() === currentMonth &&
            new Date(req.created_at).getFullYear() === currentYear
          ).length;
          const rejectedThisMonth = leaveRequests.filter(req => 
            req.status === 'REJECTED' && 
            new Date(req.created_at).getMonth() === currentMonth &&
            new Date(req.created_at).getFullYear() === currentYear
          ).length;

          setStats({
            pendingRequests,
            approvedThisMonth,
            rejectedThisMonth,
            averageProcessingTime: 2.3 // This could be calculated from actual processing times
          });
        } catch (leaveError) {
          console.warn('Could not fetch leave data for admin stats:', leaveError);
        }

      } catch (error) {
        console.error('Failed to fetch data:', error);
        setEmployees([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-xl">Loading admin dashboard...</div>
        </div>
      </Layout>
    );
  }

  const activeEmployees = employees.filter(e => e.status === 'ACTIVE').length;
  const onLeaveEmployees = employees.filter(e => e.status === 'ON_LEAVE').length;

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Organization Admin Dashboard</h1>
          <p className="text-gray-600">Welcome, {user?.first_name}! Manage your organization and oversee operations.</p>
          {/* Debug info */}
          <div className="bg-red-100 border border-red-300 rounded p-2 mt-2 text-sm">
            <strong>DEBUG:</strong> You are viewing the OrgAdminDashboard. Role: {user?.role}
          </div>
        </div>

        {/* Admin Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <span className="text-yellow-600 text-xl">⏳</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Pending Requests</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.pendingRequests}</p>
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
                <p className="text-2xl font-semibold text-gray-900">{stats.approvedThisMonth}</p>
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
                <p className="text-2xl font-semibold text-gray-900">{stats.rejectedThisMonth}</p>
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
                <p className="text-2xl font-semibold text-gray-900">{stats.averageProcessingTime} days</p>
              </div>
            </div>
          </div>
        </div>

        {/* Employee Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <span className="text-blue-600 text-xl">👥</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Employees</p>
                <p className="text-2xl font-semibold text-gray-900">{employees.length}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <span className="text-green-600 text-xl">✅</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Employees</p>
                <p className="text-2xl font-semibold text-gray-900">{activeEmployees}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <span className="text-yellow-600 text-xl">📅</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">On Leave</p>
                <p className="text-2xl font-semibold text-gray-900">{onLeaveEmployees}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Admin Management Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">👤</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Employee Management</h3>
              <p className="text-sm text-gray-600 mb-4">Manage employee records and profiles</p>
              <button 
                onClick={() => navigate('/employees')}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm"
              >
                Manage Employees
              </button>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">📅</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Leave Management</h3>
              <p className="text-sm text-gray-600 mb-4">Approve and manage leave requests</p>
              <button 
                onClick={() => navigate('/leave')}
                className="w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm"
              >
                Manage Leave
              </button>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">💰</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Payroll</h3>
              <p className="text-sm text-gray-600 mb-4">Manage payroll and compensation</p>
              <button 
                onClick={() => navigate('/payroll')}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md text-sm"
              >
                Manage Payroll
              </button>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">📊</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Reports</h3>
              <p className="text-sm text-gray-600 mb-4">Generate organization reports</p>
              <button 
                onClick={() => navigate('/reports')}
                className="w-full bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-md text-sm"
              >
                View Reports
              </button>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {[
                { action: 'Leave request approved for employee', time: '1 hour ago', type: 'leave' },
                { action: 'New employee added to organization', time: '2 hours ago', type: 'employee' },
                { action: 'Payroll processed for current month', time: '3 hours ago', type: 'payroll' },
                { action: 'Training program scheduled', time: '4 hours ago', type: 'training' }
              ].map((activity, index) => (
                <div key={index} className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                      <span className="text-gray-600 text-sm">
                        {activity.type === 'leave' ? '📅' : 
                         activity.type === 'employee' ? '👤' : 
                         activity.type === 'payroll' ? '💰' : '🎓'}
                      </span>
                    </div>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{activity.action}</p>
                    <p className="text-sm text-gray-500">{activity.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default OrgAdminDashboard;
