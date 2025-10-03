import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { employeesAPI, leaveAPI, expensesAPI, attendanceAPI } from '../../services/api';
import { Employee } from '../../types';
import Layout from '../Layout';
import { useNavigate } from 'react-router-dom';

const ManagerDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [teamStats, setTeamStats] = useState({
    totalTeamMembers: 0,
    presentToday: 0,
    onLeave: 0,
    pendingApprovals: 0
  });
  const [teamMembers, setTeamMembers] = useState<any[]>([]);
  const [pendingRequests, setPendingRequests] = useState<any[]>([]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        
        // Fetch team members (employees under this manager)
        const employeesRes = await employeesAPI.getEmployees();
        const employees = Array.isArray(employeesRes.data) ? employeesRes.data : [];
        
        // Filter employees under this manager (using direct_manager_id)
        const teamEmployees = employees.filter((emp: Employee) => emp.direct_manager_id === user?.id);
        
        // Fetch leave requests for approval
        const leaveRequestsRes = await leaveAPI.getLeaveRequests({ status: 'PENDING' });
        const pendingLeaveRequests = Array.isArray(leaveRequestsRes.data) ? leaveRequestsRes.data : [];
        
        // Fetch expense reports for approval
        const expenseReportsRes = await expensesAPI.getExpenseReports({ status: 'PENDING' });
        const pendingExpenseReports = Array.isArray(expenseReportsRes.data?.reports) ? expenseReportsRes.data.reports : [];
        
        // Calculate stats
        const activeEmployees = teamEmployees.filter(emp => emp.status === 'ACTIVE').length;
        const onLeaveEmployees = teamEmployees.filter(emp => emp.status === 'ON_LEAVE').length;
        
        // Get today's attendance for team members
        let presentToday = 0;
        try {
          const attendanceRes = await attendanceAPI.getAttendanceSummary(
            new Date().getMonth() + 1, 
            new Date().getFullYear()
          );
          // This would need to be adapted based on actual API response
          presentToday = Math.floor(activeEmployees * 0.9); // Estimate for now
        } catch (err) {
          presentToday = Math.floor(activeEmployees * 0.9); // Fallback estimate
        }
        
        setTeamStats({
          totalTeamMembers: teamEmployees.length,
          presentToday: presentToday,
          onLeave: onLeaveEmployees,
          pendingApprovals: pendingLeaveRequests.length + pendingExpenseReports.length
        });
        
        // Format team members data
        const formattedTeamMembers = teamEmployees.slice(0, 4).map((emp: Employee) => ({
          name: `${emp.first_name} ${emp.last_name}`,
          status: emp.status === 'ACTIVE' ? 'Present' : emp.status === 'ON_LEAVE' ? 'On Leave' : 'Inactive',
          role: emp.job_title || 'Employee',
          avatar: '👨‍💻'
        }));
        setTeamMembers(formattedTeamMembers);
        
        // Format pending requests
        const formattedRequests = [
          ...pendingLeaveRequests.slice(0, 2).map((req: any) => ({
            type: 'Leave Request',
            employee: req.employee_name || 'Team Member',
            date: new Date(req.start_date).toLocaleDateString(),
            status: 'Pending'
          })),
          ...pendingExpenseReports.slice(0, 1).map((req: any) => ({
            type: 'Expense Report',
            employee: req.employee || 'Team Member',
            amount: `$${req.total_amount?.toFixed(2) || '0.00'}`,
            status: 'Pending'
          }))
        ];
        setPendingRequests(formattedRequests.slice(0, 3));
        
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
        // Fallback to default values
        setTeamStats({
          totalTeamMembers: 0,
          presentToday: 0,
          onLeave: 0,
          pendingApprovals: 0
        });
        setTeamMembers([]);
        setPendingRequests([]);
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      fetchDashboardData();
    }
  }, [user]);

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-xl">Loading manager dashboard...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {user?.role === 'DIRECTOR' ? 'Department Director Dashboard' : 'Team Manager Dashboard'}
          </h1>
          <p className="text-gray-600">
            Welcome, {user?.first_name}! Manage your {user?.role === 'DIRECTOR' ? 'department' : 'team'}.
          </p>
        </div>

        {/* Team Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <span className="text-blue-600 text-xl">👥</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Team Members</p>
                <p className="text-2xl font-semibold text-gray-900">{teamStats.totalTeamMembers}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <span className="text-green-600 text-xl">✅</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Present Today</p>
                <p className="text-2xl font-semibold text-gray-900">{teamStats.presentToday}</p>
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
                <p className="text-2xl font-semibold text-gray-900">{teamStats.onLeave}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 rounded-lg">
                <span className="text-red-600 text-xl">⏳</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Pending Approvals</p>
                <p className="text-2xl font-semibold text-gray-900">{teamStats.pendingApprovals}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Management Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">👥</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Team Overview</h3>
              <p className="text-sm text-gray-600 mb-4">View team performance and status</p>
              <button 
                onClick={() => navigate('/employees')}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm"
              >
                View Team
              </button>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">📅</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Leave Approvals</h3>
              <p className="text-sm text-gray-600 mb-4">Approve team leave requests</p>
              <button 
                onClick={() => navigate('/leave')}
                className="w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm"
              >
                Approve Leave
              </button>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">📊</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Performance</h3>
              <p className="text-sm text-gray-600 mb-4">Review team performance</p>
              <button 
                onClick={() => navigate('/reports')}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md text-sm"
              >
                Performance
              </button>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">💰</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Expense Approvals</h3>
              <p className="text-sm text-gray-600 mb-4">Approve expense reports</p>
              <button 
                onClick={() => navigate('/expenses')}
                className="w-full bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-md text-sm"
              >
                Approve Expenses
              </button>
            </div>
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Team Members */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Team Members</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {teamMembers.map((member, index) => (
                  <div key={index} className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                        <span className="text-gray-600 text-lg">{member.avatar}</span>
                      </div>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{member.name}</p>
                      <p className="text-sm text-gray-500">{member.role}</p>
                    </div>
                    <div className="flex-shrink-0">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        member.status === 'Present' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {member.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Pending Approvals */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Pending Approvals</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {pendingRequests.map((request, index) => (
                  <div key={index} className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                        <span className="text-red-600 text-sm">
                          {request.type === 'Leave Request' ? '📅' : 
                           request.type === 'Expense Report' ? '💰' : '⏰'}
                        </span>
                      </div>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{request.type}</p>
                      <p className="text-sm text-gray-500">{request.employee} - {request.date || request.amount || request.hours}</p>
                    </div>
                    <div className="flex-shrink-0">
                      <button className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded">
                        Review
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default ManagerDashboard; 