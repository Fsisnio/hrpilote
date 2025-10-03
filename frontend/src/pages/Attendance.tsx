import React, { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout';
import { attendanceAPI } from '../services/api';
import Toast from '../components/Toast';
import { useAuth } from '../contexts/AuthContext';

interface AttendanceRecord {
  id: number;
  date: string;
  clock_in_time: string;
  clock_out_time: string | null;
  total_hours: number | null;
  status: string;
  breaks: BreakRecord[];
}

interface BreakRecord {
  id: number;
  break_start: string;
  break_end: string | null;
  duration_minutes: number | null;
  break_type: string;
}

interface TodaySummary {
  clockIn: string | null;
  clockOut: string | null;
  totalHours: number;
  breakHours: number;
  netHours: number;
  isClockedIn: boolean;
  isOnBreak: boolean;
}

const Attendance: React.FC = () => {
  const { user } = useAuth();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [loading, setLoading] = useState(false);
  const [, setTodayAttendance] = useState<AttendanceRecord | null>(null);
  const [attendanceHistory, setAttendanceHistory] = useState<AttendanceRecord[]>([]);
  const [todaySummary, setTodaySummary] = useState<TodaySummary>({
    clockIn: null,
    clockOut: null,
    totalHours: 0,
    breakHours: 0,
    netHours: 0,
    isClockedIn: false,
    isOnBreak: false
  });
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastType, setToastType] = useState<'success' | 'error' | 'info'>('success');
  const [employeeRecordMissing, setEmployeeRecordMissing] = useState(false);

  const fetchTodayAttendance = useCallback(async () => {
    try {
      const response = await attendanceAPI.getTodayAttendance();
      const attendance = response.data;
      setTodayAttendance(attendance);
      setEmployeeRecordMissing(false);
      
      // Calculate today's summary
      const clockIn = attendance.clock_in_time ? new Date(attendance.clock_in_time).toLocaleTimeString() : null;
      const clockOut = attendance.clock_out_time ? new Date(attendance.clock_out_time).toLocaleTimeString() : null;
      const totalHours = attendance.total_hours || 0;
      const breakHours = attendance.breaks?.reduce((total: number, breakRecord: BreakRecord) => {
        return total + (breakRecord.duration_minutes || 0) / 60;
      }, 0) || 0;
      
      setTodaySummary({
        clockIn,
        clockOut,
        totalHours,
        breakHours,
        netHours: totalHours - breakHours,
        isClockedIn: !!attendance.clock_in_time && !attendance.clock_out_time,
        isOnBreak: attendance.breaks?.some((b: BreakRecord) => !b.break_end) || false
      });
    } catch (error: any) {
      if (error.response?.status === 403) {
        // User role doesn't support attendance tracking
        displayToast(`Attendance tracking is not available for ${user?.role} role`, 'info');
      } else if (error.response?.status === 404 && error.response?.data?.detail?.includes('Employee record not found')) {
        // Employee role but no employee record - show helpful message
        setEmployeeRecordMissing(true);
        displayToast('Employee profile not set up. Please contact HR.', 'info');
      } else if (error.response?.status !== 404) {
        displayToast('Failed to fetch today\'s attendance', 'error');
      }
    }
  }, [user?.role]);

  const fetchAttendanceHistory = useCallback(async () => {
    try {
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - 30); // Last 30 days
      const endDate = new Date();
      
      const response = await attendanceAPI.getAttendanceHistory(
        startDate.toISOString().split('T')[0],
        endDate.toISOString().split('T')[0]
      );
      setAttendanceHistory(response.data);
    } catch (error: any) {
      if (error.response?.status === 403) {
        // User role doesn't support attendance tracking
        displayToast(`Attendance tracking is not available for ${user?.role} role`, 'info');
      } else if (error.response?.status === 404 && error.response?.data?.detail?.includes('Employee record not found')) {
        // Employee role but no employee record - show helpful message
        displayToast('Employee profile not set up. Please contact HR.', 'info');
      } else {
        displayToast('Failed to fetch attendance history', 'error');
      }
    }
  }, [user?.role]);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    if (user) {
      fetchTodayAttendance();
      fetchAttendanceHistory();
    }

    return () => clearInterval(timer);
  }, [user, fetchTodayAttendance, fetchAttendanceHistory]);

  const handleClockIn = async () => {
    setLoading(true);
    try {
      const clockInData = {
        location: 'Office',
        ip_address: '127.0.0.1'
      };
      
      await attendanceAPI.clockIn(clockInData);
      await fetchTodayAttendance();
      displayToast('Successfully clocked in!', 'success');
    } catch (error: any) {
      if (error.response?.status === 404 && error.response?.data?.detail?.includes('Employee record not found')) {
        setEmployeeRecordMissing(true);
        displayToast('Employee profile not set up. Please contact HR.', 'error');
      } else {
        displayToast(error.response?.data?.detail || 'Failed to clock in', 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClockOut = async () => {
    setLoading(true);
    try {
      const clockOutData = {
        location: 'Office',
        ip_address: '127.0.0.1'
      };
      
      await attendanceAPI.clockOut(clockOutData);
      await fetchTodayAttendance();
      displayToast('Successfully clocked out!', 'success');
    } catch (error: any) {
      if (error.response?.status === 404 && error.response?.data?.detail?.includes('Employee record not found')) {
        setEmployeeRecordMissing(true);
        displayToast('Employee profile not set up. Please contact HR.', 'error');
      } else {
        displayToast(error.response?.data?.detail || 'Failed to clock out', 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleBreak = async () => {
    setLoading(true);
    try {
      if (todaySummary.isOnBreak) {
        await attendanceAPI.endBreak();
        displayToast('Break ended successfully!', 'success');
      } else {
        const breakData = {
          break_type: 'LUNCH',
          location: 'Office',
          notes: 'Lunch break'
        };
        await attendanceAPI.startBreak(breakData);
        displayToast('Break started successfully!', 'success');
      }
      await fetchTodayAttendance();
    } catch (error: any) {
      if (error.response?.status === 404 && error.response?.data?.detail?.includes('Employee record not found')) {
        setEmployeeRecordMissing(true);
        displayToast('Employee profile not set up. Please contact HR.', 'error');
      } else {
        displayToast(error.response?.data?.detail || 'Failed to handle break', 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  const displayToast = (message: string, type: 'success' | 'error' | 'info') => {
    setToastMessage(message);
    setToastType(type);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  const formatTime = (timeString: string) => {
    return new Date(timeString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatHours = (hours: number) => {
    const wholeHours = Math.floor(hours);
    const minutes = Math.round((hours - wholeHours) * 60);
    return `${wholeHours}h ${minutes}m`;
  };

  const getWeekData = () => {
    const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const today = new Date();
    const startOfWeek = new Date(today);
    startOfWeek.setDate(today.getDate() - today.getDay() + 1); // Monday
    
    return weekDays.map((day, index) => {
      const date = new Date(startOfWeek);
      date.setDate(startOfWeek.getDate() + index);
      const dateStr = date.toISOString().split('T')[0];
      
      const record = attendanceHistory.find(r => r.date === dateStr);
      
      if (record) {
        return {
          day,
          clockIn: record.clock_in_time ? formatTime(record.clock_in_time) : '--',
          clockOut: record.clock_out_time ? formatTime(record.clock_out_time) : '--',
          totalHours: record.total_hours ? formatHours(record.total_hours) : '--'
        };
      }
      
      return {
        day,
        clockIn: '--',
        clockOut: '--',
        totalHours: '--'
      };
    });
  };

  // Show loading or redirect if user is not authenticated
  if (!user) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <div className="text-xl font-semibold text-gray-600 mb-4">
              Please log in to access attendance tracking
            </div>
            <button 
              onClick={() => window.location.href = '/login'}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md"
            >
              Go to Login
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  // Check if user role supports attendance tracking
  const isEmployeeRole = user.role === 'EMPLOYEE';

  // Show special interface for employees without employee records
  if (isEmployeeRole && employeeRecordMissing) {
    return (
      <Layout>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Attendance & Time Tracking</h1>
              <p className="text-gray-600">Track your work hours and attendance</p>
            </div>
          </div>

          {/* Employee Record Missing Message */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  Employee Profile Setup Required
                </h3>
                <div className="mt-2 text-sm text-yellow-700">
                  <p>
                    Your user account has employee privileges, but your employee profile hasn't been set up yet. 
                    This is required to track attendance and manage your work hours.
                  </p>
                  <p className="mt-2">
                    Please contact your HR department or system administrator to complete your employee profile setup.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <button 
              onClick={() => window.location.href = '/dashboard'}
              className="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-lg text-center transition-colors"
            >
              <div className="text-2xl mb-2">🏠</div>
              <div className="font-medium">Go to Dashboard</div>
            </button>
            <button 
              onClick={() => window.location.href = '/documents'}
              className="bg-green-600 hover:bg-green-700 text-white p-4 rounded-lg text-center transition-colors"
            >
              <div className="text-2xl mb-2">📄</div>
              <div className="font-medium">View Documents</div>
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  // Show different interface for non-employee users
  if (!isEmployeeRole) {
    return (
      <Layout>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Attendance & Time Tracking</h1>
              <p className="text-gray-600">Employee attendance management</p>
            </div>
          </div>

          {/* Non-Employee Message */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">
                  Attendance Tracking Not Available
                </h3>
                <div className="mt-2 text-sm text-blue-700">
                  <p>
                    As a <span className="font-semibold">{user.role}</span>, attendance tracking is not available for your role. 
                    This feature is designed for employees to track their work hours and attendance.
                  </p>
                  <p className="mt-2">
                    You can access other HR management features from the navigation menu.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions for Admins */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <button 
              onClick={() => window.location.href = '/employees'}
              className="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-lg text-center transition-colors"
            >
              <div className="text-2xl mb-2">👥</div>
              <div className="font-medium">Manage Employees</div>
            </button>
            <button 
              onClick={() => window.location.href = '/reports'}
              className="bg-green-600 hover:bg-green-700 text-white p-4 rounded-lg text-center transition-colors"
            >
              <div className="text-2xl mb-2">📊</div>
              <div className="font-medium">View Reports</div>
            </button>
            <button 
              onClick={() => window.location.href = '/dashboard'}
              className="bg-purple-600 hover:bg-purple-700 text-white p-4 rounded-lg text-center transition-colors"
            >
              <div className="text-2xl mb-2">📈</div>
              <div className="font-medium">Dashboard</div>
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
            <h1 className="text-2xl font-bold text-gray-900">Attendance & Time Tracking</h1>
            <p className="text-gray-600">Track your work hours and attendance</p>
          </div>
        </div>

        {/* Current Time and Clock In/Out */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Current Time Card */}
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-center">
              <div className="text-4xl font-bold text-gray-900 mb-2">
                {currentTime.toLocaleTimeString()}
              </div>
              <div className="text-lg text-gray-600">
                {currentTime.toLocaleDateString()}
              </div>
              <div className="text-sm text-gray-500 mt-2">
                {currentTime.toLocaleDateString('en-US', { weekday: 'long' })}
              </div>
            </div>
          </div>

          {/* Clock In/Out Card */}
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-center">
              <div className="text-2xl font-semibold text-gray-900 mb-4">
                {todaySummary.isClockedIn ? 'Currently Clocked In' : 'Not Clocked In'}
              </div>
              <div className="space-y-3">
                {!todaySummary.isClockedIn ? (
                  <button
                    onClick={handleClockIn}
                    disabled={loading}
                    className="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-3 rounded-md font-medium"
                  >
                    {loading ? 'Clocking In...' : 'Clock In'}
                  </button>
                ) : (
                  <button
                    onClick={handleClockOut}
                    disabled={loading}
                    className="w-full bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white px-4 py-3 rounded-md font-medium"
                  >
                    {loading ? 'Clocking Out...' : 'Clock Out'}
                  </button>
                )}
                {todaySummary.isClockedIn && (
                  <button
                    onClick={handleBreak}
                    disabled={loading}
                    className={`w-full px-4 py-2 rounded-md font-medium ${
                      todaySummary.isOnBreak
                        ? 'bg-orange-600 hover:bg-orange-700 disabled:bg-orange-400 text-white'
                        : 'bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-400 text-white'
                    }`}
                  >
                    {loading ? 'Processing...' : todaySummary.isOnBreak ? 'End Break' : 'Start Break'}
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Today's Summary */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Today's Summary</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Clock In:</span>
                <span className="font-medium">{todaySummary.clockIn || '--'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Clock Out:</span>
                <span className="font-medium">{todaySummary.clockOut || '--'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Hours:</span>
                <span className="font-medium">{formatHours(todaySummary.totalHours)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Breaks:</span>
                <span className="font-medium">{formatHours(todaySummary.breakHours)}</span>
              </div>
              <div className="flex justify-between border-t pt-2">
                <span className="text-gray-900 font-medium">Net Hours:</span>
                <span className="font-bold text-green-600">{formatHours(todaySummary.netHours)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Weekly Overview */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">This Week's Attendance</h3>
          <div className="grid grid-cols-7 gap-4">
            {getWeekData().map((dayData, index) => (
              <div key={dayData.day} className="text-center">
                <div className="text-sm font-medium text-gray-600 mb-2">{dayData.day}</div>
                <div className="bg-gray-100 rounded-lg p-3">
                  <div className="text-xs text-gray-500">In</div>
                  <div className="text-sm font-medium">{dayData.clockIn}</div>
                  <div className="text-xs text-gray-500 mt-1">Out</div>
                  <div className="text-sm font-medium">{dayData.clockOut}</div>
                  <div className="text-xs text-green-600 mt-1 font-medium">{dayData.totalHours}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Attendance Records */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Recent Attendance Records</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Clock In
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Clock Out
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Hours
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Breaks
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {attendanceHistory.slice(0, 10).map((record, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(record.date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {record.clock_in_time ? formatTime(record.clock_in_time) : '--'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {record.clock_out_time ? formatTime(record.clock_out_time) : '--'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {record.total_hours ? formatHours(record.total_hours) : '--'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {record.breaks ? formatHours(record.breaks.reduce((total, b) => total + (b.duration_minutes || 0) / 60, 0)) : '0h 0m'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        record.status === 'PRESENT' 
                          ? 'bg-green-100 text-green-800' 
                          : record.status === 'LATE'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {record.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <button className="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-lg text-center">
            <div className="text-2xl mb-2">📊</div>
            <div className="font-medium">View Reports</div>
          </button>
          <button className="bg-green-600 hover:bg-green-700 text-white p-4 rounded-lg text-center">
            <div className="text-2xl mb-2">📅</div>
            <div className="font-medium">Request Time Off</div>
          </button>
          <button className="bg-purple-600 hover:bg-purple-700 text-white p-4 rounded-lg text-center">
            <div className="text-2xl mb-2">⚙️</div>
            <div className="font-medium">Settings</div>
          </button>
        </div>
      </div>

      {/* Toast Notification */}
      <Toast
        message={toastMessage}
        type={toastType}
        isVisible={showToast}
        onClose={() => setShowToast(false)}
      />
    </Layout>
  );
};

export default Attendance; 