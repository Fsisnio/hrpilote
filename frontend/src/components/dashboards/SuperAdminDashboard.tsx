import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { usersAPI, organizationsAPI } from '../../services/api';
import { User, Organization } from '../../types';
import Layout from '../Layout';
import { useNavigate } from 'react-router-dom';

const SuperAdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [usersRes, orgsRes] = await Promise.all([
          usersAPI.getUsers(),
          organizationsAPI.getOrganizations(),
        ]);
        
        setUsers(Array.isArray(usersRes.data) ? usersRes.data : []);
        setOrganizations(Array.isArray(orgsRes.data) ? orgsRes.data : []);
      } catch (error) {
        console.error('Failed to fetch data:', error);
        setUsers([]);
        setOrganizations([]);
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
          <div className="text-xl">Loading system dashboard...</div>
        </div>
      </Layout>
    );
  }

  const activeUsers = users.filter(u => u.is_active).length;
  const inactiveUsers = users.filter(u => !u.is_active).length;
  const activeOrganizations = organizations.filter(o => o.status === 'ACTIVE').length;

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Administration Dashboard</h1>
          <p className="text-gray-600">Welcome, {user?.first_name}! You have full system access.</p>
        </div>

        {/* System Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 rounded-lg">
                <span className="text-red-600 text-xl">👑</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Organizations</p>
                <p className="text-2xl font-semibold text-gray-900">{organizations.length}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <span className="text-blue-600 text-xl">👥</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Users</p>
                <p className="text-2xl font-semibold text-gray-900">{users.length}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <span className="text-green-600 text-xl">✅</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Users</p>
                <p className="text-2xl font-semibold text-gray-900">{activeUsers}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <span className="text-yellow-600 text-xl">⚠️</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Inactive Users</p>
                <p className="text-2xl font-semibold text-gray-900">{inactiveUsers}</p>
              </div>
            </div>
          </div>
        </div>

        {/* System Management Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">🏢</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Manage Organizations</h3>
              <p className="text-sm text-gray-600 mb-4">Create and manage organizations</p>
              <button 
                onClick={() => navigate('/organizations')}
                className="w-full bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm"
              >
                Manage Orgs
              </button>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">👥</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">System Users</h3>
              <p className="text-sm text-gray-600 mb-4">Manage all system users</p>
              <button 
                onClick={() => navigate('/users')}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm"
              >
                View Users
              </button>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">⚙️</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">System Settings</h3>
              <p className="text-sm text-gray-600 mb-4">Configure system-wide settings</p>
              <button 
                onClick={() => navigate('/reports')}
                className="w-full bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm"
              >
                Settings
              </button>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="text-3xl mb-4">📊</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">System Analytics</h3>
              <p className="text-sm text-gray-600 mb-4">View system-wide analytics</p>
              <button 
                onClick={() => navigate('/reports')}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md text-sm"
              >
                Analytics
              </button>
            </div>
          </div>
        </div>

        {/* System Activity */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">System Activity</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {[
                { action: 'New organization "TechCorp" registered', time: '1 hour ago', type: 'organization' },
                { action: 'System backup completed successfully', time: '2 hours ago', type: 'system' },
                { action: 'User account locked due to security policy', time: '3 hours ago', type: 'security' },
                { action: 'System maintenance scheduled for tonight', time: '4 hours ago', type: 'maintenance' }
              ].map((activity, index) => (
                <div key={index} className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                      <span className="text-gray-600 text-sm">
                        {activity.type === 'organization' ? '🏢' : 
                         activity.type === 'system' ? '⚙️' : 
                         activity.type === 'security' ? '🔒' : '🔧'}
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

export default SuperAdminDashboard; 