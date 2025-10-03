import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { payrollAPI, employeesAPI } from '../../services/api';
import Layout from '../Layout';
import { useNavigate } from 'react-router-dom';
import Toast from '../Toast';

const PayrollDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [payrollStats, setPayrollStats] = useState({
    totalEmployees: 0,
    processedThisMonth: 0,
    pendingApproval: 0,
    totalPayroll: 0
  });
  const [recentPayrollActivity, setRecentPayrollActivity] = useState<any[]>([]);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info'; isVisible: boolean }>({
    message: '',
    type: 'info',
    isVisible: false
  });

  const showToast = (message: string, type: 'success' | 'error' | 'info') => {
    setToast({ message, type, isVisible: true });
  };

  const handleProcessPayroll = async () => {
    setIsProcessing(true);
    showToast('Processing payroll...', 'info');
    
    try {
      await payrollAPI.processPayroll();
      setIsProcessing(false);
      showToast('Payroll processed successfully!', 'success');
      // Refresh data after processing
      fetchDashboardData();
    } catch (error) {
      setIsProcessing(false);
      showToast('Failed to process payroll. Please try again.', 'error');
    }
  };

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch payroll summary
      const payrollSummaryRes = await payrollAPI.getPayrollSummary();
      const payrollSummary = payrollSummaryRes.data || {};
      
      // Fetch employees count
      const employeesRes = await employeesAPI.getEmployees();
      const employees = Array.isArray(employeesRes.data) ? employeesRes.data : [];
      const activeEmployees = employees.filter((emp: any) => emp.status === 'ACTIVE').length;
      
      // Fetch recent payroll activity
      const activityRes = await payrollAPI.getPayrollActivity(5);
      const activities = Array.isArray(activityRes.data) ? activityRes.data : [];
      
      setPayrollStats({
        totalEmployees: activeEmployees,
        processedThisMonth: payrollSummary.processed_this_month || 0,
        pendingApproval: payrollSummary.pending_approval || 0,
        totalPayroll: payrollSummary.total_payroll || 0
      });
      
      // Format recent activity
      const formattedActivities = activities.map((activity: any) => ({
        action: activity.description || activity.action || 'Payroll activity',
        time: activity.created_at ? new Date(activity.created_at).toLocaleDateString() : 'Recently',
        type: activity.type || 'processed'
      }));
      
      // Fallback to mock data if no real data
      if (formattedActivities.length === 0) {
        setRecentPayrollActivity([
          { action: 'Payroll system initialized', time: 'Today', type: 'processed' },
          { action: 'Employee data synchronized', time: 'Today', type: 'sync' }
        ]);
      } else {
        setRecentPayrollActivity(formattedActivities);
      }
      
    } catch (error) {
      console.error('Failed to fetch payroll data:', error);
      // Fallback to default values
      setPayrollStats({
        totalEmployees: 0,
        processedThisMonth: 0,
        pendingApproval: 0,
        totalPayroll: 0
      });
      setRecentPayrollActivity([
        { action: 'System initialized', time: 'Today', type: 'processed' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchDashboardData();
    }
  }, [user]);

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-xl">Loading payroll dashboard...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Payroll Management Dashboard</h1>
          <p className="text-gray-600">Welcome, {user?.first_name}! Manage payroll and compensation.</p>
        </div>

        {/* Payroll Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <span className="text-blue-600 text-xl">👥</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Employees</p>
                <p className="text-2xl font-semibold text-gray-900">{payrollStats.totalEmployees}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <span className="text-green-600 text-xl">✅</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Processed This Month</p>
                <p className="text-2xl font-semibold text-gray-900">{payrollStats.processedThisMonth}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <span className="text-yellow-600 text-xl">⏳</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Pending Approval</p>
                <p className="text-2xl font-semibold text-gray-900">{payrollStats.pendingApproval}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <span className="text-purple-600 text-xl">💰</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Payroll</p>
                <p className="text-2xl font-semibold text-gray-900">${payrollStats.totalPayroll.toLocaleString()}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Payroll Management Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">💰</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Process Payroll</h3>
              <p className="text-sm text-gray-600 mb-4">Run monthly payroll processing</p>
              <button 
                onClick={handleProcessPayroll}
                disabled={isProcessing}
                className={`w-full px-4 py-2 rounded-md text-sm font-medium ${
                  isProcessing 
                    ? 'bg-gray-400 cursor-not-allowed' 
                    : 'bg-green-600 hover:bg-green-700'
                } text-white`}
              >
                {isProcessing ? 'Processing...' : 'Process Payroll'}
              </button>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">📊</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Payroll Reports</h3>
              <p className="text-sm text-gray-600 mb-4">Generate payroll reports</p>
              <button 
                onClick={() => navigate('/reports')}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm"
              >
                View Reports
              </button>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">🏦</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Tax Management</h3>
              <p className="text-sm text-gray-600 mb-4">Manage tax calculations</p>
              <button 
                onClick={() => navigate('/payroll')}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md text-sm"
              >
                Tax Center
              </button>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">⚙️</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Salary Structure</h3>
              <p className="text-sm text-gray-600 mb-4">Manage salary components</p>
              <button 
                onClick={() => navigate('/payroll')}
                className="w-full bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm"
              >
                Salary Config
              </button>
            </div>
          </div>
        </div>

        {/* Payroll Activity */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Payroll Activity</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {recentPayrollActivity.map((activity, index) => (
                <div key={index} className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                      <span className="text-gray-600 text-sm">
                        {activity.type === 'processed' ? '✅' : 
                         activity.type === 'bonus' ? '🎁' : 
                         activity.type === 'tax' ? '🏦' : '💰'}
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
      <Toast
        message={toast.message}
        type={toast.type}
        isVisible={toast.isVisible}
        onClose={() => setToast(prev => ({ ...prev, isVisible: false }))}
      />
    </Layout>
  );
};

export default PayrollDashboard; 