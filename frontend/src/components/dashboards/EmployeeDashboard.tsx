import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import Layout from '../Layout';
import { useNavigate } from 'react-router-dom';
import Toast from '../Toast';
import { leaveAPI, attendanceAPI, trainingAPI } from '../../services/api';

const EmployeeDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [isClockedIn, setIsClockedIn] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info'; isVisible: boolean }>({
    message: '',
    type: 'info',
    isVisible: false
  });

  // Dynamic data state
  const [leaveBalances, setLeaveBalances] = useState<any[]>([]);
  const [attendanceData, setAttendanceData] = useState<any>(null);
  const [trainingData, setTrainingData] = useState<any>(null);
  const [recentActivity, setRecentActivity] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const showToast = (message: string, type: 'success' | 'error' | 'info') => {
    setToast({ message, type, isVisible: true });
  };

  const handleClockInOut = async () => {
    setLoading(true);
    try {
      if (isClockedIn) {
        // Clock out
        await attendanceAPI.clockOut({
          location: 'Office', // You can get this from user's location or make it configurable
          ip_address: '127.0.0.1' // You can get the actual IP if needed
        });
        setIsClockedIn(false);
        showToast('Successfully clocked out!', 'success');
      } else {
        // Clock in
        await attendanceAPI.clockIn({
          location: 'Office', // You can get this from user's location or make it configurable
          ip_address: '127.0.0.1' // You can get the actual IP if needed
        });
        setIsClockedIn(true);
        showToast('Successfully clocked in!', 'success');
      }
      // Refresh attendance data after clock in/out
      await fetchDashboardData();
    } catch (error: any) {
      console.error('Clock in/out error:', error);
      showToast(
        error.response?.data?.detail || 
        (isClockedIn ? 'Failed to clock out' : 'Failed to clock in'), 
        'error'
      );
    } finally {
      setLoading(false);
    }
  };

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch leave balances
      try {
        const leaveResponse = await leaveAPI.getLeaveBalancesSummary();
        setLeaveBalances(leaveResponse.data || []);
      } catch (err) {
        console.error('Error fetching leave balances:', err);
        setLeaveBalances([]);
      }

      // Fetch today's attendance
      try {
        const attendanceResponse = await attendanceAPI.getTodayAttendance();
        setAttendanceData(attendanceResponse.data);
        // Check if user is clocked in (has clock_in_time but no clock_out_time)
        const isClockedIn = attendanceResponse.data?.clock_in_time && !attendanceResponse.data?.clock_out_time;
        setIsClockedIn(isClockedIn);
      } catch (err) {
        console.error('Error fetching attendance:', err);
        setAttendanceData(null);
        setIsClockedIn(false);
      }

      // Fetch training summary
      try {
        const trainingResponse = await trainingAPI.getTrainingSummary();
        setTrainingData(trainingResponse.data);
      } catch (err) {
        console.error('Error fetching training data:', err);
        setTrainingData(null);
      }

      // Build recent activity from various sources
      const activities = [];
      
      // Add attendance activity
      if (attendanceData?.last_clock_in) {
        activities.push({
          action: 'Last clock in',
          time: new Date(attendanceData.last_clock_in).toLocaleDateString(),
          type: 'attendance'
        });
      }

      // Add training activity
      if (trainingData?.recent_enrollments) {
        trainingData.recent_enrollments.forEach((enrollment: any) => {
          activities.push({
            action: `Enrolled in ${enrollment.course_title}`,
            time: new Date(enrollment.enrollment_date).toLocaleDateString(),
            type: 'training'
          });
        });
      }

      setRecentActivity(activities.slice(0, 5)); // Limit to 5 recent activities

    } catch (err: any) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch dynamic data
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <div className="text-xl">Loading dashboard...</div>
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
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Dashboard</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={fetchDashboardData}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md"
          >
            Retry
          </button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Employee Dashboard</h1>
          <p className="text-gray-600">Welcome back, {user?.first_name}! Here's your personal overview.</p>
        </div>

        {/* Personal Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <span className="text-green-600 text-xl">✅</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Status</p>
                <p className="text-2xl font-semibold text-gray-900">Active</p>
              </div>
            </div>
          </div>
          {leaveBalances.length > 0 ? (
            leaveBalances.slice(0, 2).map((balance) => (
              <div key={balance.type} className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <span className="text-blue-600 text-xl">📅</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">{balance.type} Leave</p>
                    <p className="text-2xl font-semibold text-gray-900">{balance.remaining} days</p>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <>
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <span className="text-blue-600 text-xl">📅</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Annual Leave</p>
                    <p className="text-2xl font-semibold text-gray-900">-</p>
                  </div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-yellow-100 rounded-lg">
                    <span className="text-yellow-600 text-xl">🏥</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Sick Leave</p>
                    <p className="text-2xl font-semibold text-gray-900">-</p>
                  </div>
                </div>
              </div>
            </>
          )}
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <span className="text-purple-600 text-xl">⏰</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Hours Today</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {attendanceData?.hours_worked_today || '0.0'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">⏰</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Clock In/Out</h3>
              <p className="text-sm text-gray-600 mb-4">Record your work hours</p>
              <button 
                onClick={handleClockInOut}
                disabled={loading}
                className={`w-full px-4 py-2 rounded-md text-sm font-medium ${
                  isClockedIn 
                    ? 'bg-red-600 hover:bg-red-700 text-white' 
                    : 'bg-green-600 hover:bg-green-700 text-white'
                } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {loading ? 'Processing...' : (isClockedIn ? 'Clock Out' : 'Clock In')}
              </button>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">📅</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Request Leave</h3>
              <p className="text-sm text-gray-600 mb-4">Submit leave requests</p>
              <button 
                onClick={() => navigate('/leave')}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm"
              >
                Request Leave
              </button>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">📄</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Documents</h3>
              <p className="text-sm text-gray-600 mb-4">Access your documents</p>
              <button 
                onClick={() => navigate('/documents')}
                className="w-full bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm"
              >
                View Documents
              </button>
            </div>
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Training Progress */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Training Progress</h3>
            </div>
            <div className="p-6">
              {trainingData ? (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-600">Courses Enrolled</span>
                    <span className="text-sm font-semibold text-gray-900">{trainingData.total_enrollments || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-600">Completed</span>
                    <span className="text-sm font-semibold text-gray-900">{trainingData.completed_courses || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-600">In Progress</span>
                    <span className="text-sm font-semibold text-gray-900">{trainingData.in_progress_courses || 0}</span>
                  </div>
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-gray-500 text-sm">No training data available</p>
                </div>
              )}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {recentActivity.length > 0 ? (
                  recentActivity.map((activity, index) => (
                    <div key={index} className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                          <span className="text-gray-600 text-sm">
                            {activity.type === 'attendance' ? '⏰' : 
                             activity.type === 'leave' ? '📅' : 
                             activity.type === 'training' ? '🎓' : '💰'}
                          </span>
                        </div>
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">{activity.action}</p>
                        <p className="text-sm text-gray-500">{activity.time}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-4">
                    <p className="text-gray-500 text-sm">No recent activity</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
      <Toast
        message={toast.message}
        type={toast.type}
        isVisible={toast.isVisible}
        onClose={() => setToast(prev => ({ ...prev, isVisible: false }))}
      />
    </Layout>
  );
};

export default EmployeeDashboard; 