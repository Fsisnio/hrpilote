import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { employeesAPI } from '../../services/api';
import { Employee } from '../../types';
import Layout from '../Layout';
import { useNavigate } from 'react-router-dom';

const HRDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const employeesRes = await employeesAPI.getEmployees();
        setEmployees(Array.isArray(employeesRes.data) ? employeesRes.data : []);
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
          <div className="text-xl">Loading HR dashboard...</div>
        </div>
      </Layout>
    );
  }

  const activeEmployees = employees.filter(e => e.status === 'ACTIVE').length;
  const onLeaveEmployees = employees.filter(e => e.status === 'ON_LEAVE').length;
  const newHires = employees.filter(e => {
    const hireDate = new Date(e.hire_date);
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    return hireDate > thirtyDaysAgo;
  }).length;

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">HR Management Dashboard</h1>
          <p className="text-gray-600">Welcome, {user?.first_name}! Manage your organization's human resources.</p>
        </div>

        {/* HR Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
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
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <span className="text-purple-600 text-xl">🆕</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">New Hires (30d)</p>
                <p className="text-2xl font-semibold text-gray-900">{newHires}</p>
              </div>
            </div>
          </div>
        </div>

        {/* HR Management Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">👤</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Employee Records</h3>
              <p className="text-sm text-gray-600 mb-4">Manage employee information</p>
              <button 
                onClick={() => navigate('/employees')}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm"
              >
                View Employees
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
              <div className="text-3xl mb-4">📊</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">HR Reports</h3>
              <p className="text-sm text-gray-600 mb-4">Generate HR analytics and reports</p>
              <button 
                onClick={() => navigate('/reports')}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md text-sm"
              >
                View Reports
              </button>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">🎓</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Training</h3>
              <p className="text-sm text-gray-600 mb-4">Manage training programs</p>
              <button 
                onClick={() => navigate('/training')}
                className="w-full bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-md text-sm"
              >
                Training
              </button>
            </div>
          </div>
        </div>

        {/* HR Activity */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">HR Activity</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {[
                { action: 'Leave request approved for John Smith', time: '1 hour ago', type: 'leave' },
                { action: 'New employee onboarding completed', time: '2 hours ago', type: 'onboarding' },
                { action: 'Performance review scheduled', time: '3 hours ago', type: 'performance' },
                { action: 'Training program updated', time: '4 hours ago', type: 'training' }
              ].map((activity, index) => (
                <div key={index} className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                      <span className="text-gray-600 text-sm">
                        {activity.type === 'leave' ? '📅' : 
                         activity.type === 'onboarding' ? '👤' : 
                         activity.type === 'performance' ? '📊' : '🎓'}
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

export default HRDashboard; 