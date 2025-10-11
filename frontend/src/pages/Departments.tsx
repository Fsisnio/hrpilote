import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { departmentsAPI } from '../services/api';
import { Department } from '../types';

const Departments: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [departments, setDepartments] = useState<Department[]>([]);
  const [summary, setSummary] = useState({
    total_departments: 0,
    total_employees: 0,
    total_budget: 0,
    average_budget: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDepartments();
    fetchSummary();
  }, []);

  const fetchDepartments = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await departmentsAPI.getDepartments({
        search: searchTerm || undefined
      });
      
      setDepartments(response.data);
    } catch (err: any) {
      console.error('Error fetching departments:', err);
      setError(err.response?.data?.detail || 'Failed to fetch departments');
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await departmentsAPI.getDepartmentsSummary();
      setSummary(response.data);
    } catch (err: any) {
      console.error('Error fetching departments summary:', err);
    }
  };

  useEffect(() => {
    if (searchTerm !== '') {
      const timeoutId = setTimeout(() => {
        fetchDepartments();
      }, 500); // Debounce search
      
      return () => clearTimeout(timeoutId);
    } else {
      fetchDepartments();
    }
  }, [searchTerm]);

  const filteredDepartments = departments.filter(dept =>
    dept.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    dept.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (dept.description && dept.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (loading && departments.length === 0) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <span className="text-red-400 text-xl">⚠️</span>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading departments</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
              <button
                onClick={() => {
                  setError(null);
                  fetchDepartments();
                  fetchSummary();
                }}
                className="mt-2 bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded text-sm"
              >
                Retry
              </button>
            </div>
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
            <h1 className="text-2xl font-bold text-gray-900">Department Management</h1>
            <p className="text-gray-600">Manage organizational departments and structure</p>
          </div>
          <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md">
            Add New Department
          </button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <span className="text-blue-600 text-xl">🏗️</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Departments</p>
                <p className="text-2xl font-semibold text-gray-900">{summary.total_departments}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <span className="text-green-600 text-xl">👥</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Employees</p>
                <p className="text-2xl font-semibold text-gray-900">{summary.total_employees}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <span className="text-purple-600 text-xl">💰</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Budget</p>
                <p className="text-2xl font-semibold text-gray-900">${(summary.total_budget / 1000000).toFixed(1)}M</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <span className="text-yellow-600 text-xl">📊</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg. Budget</p>
                <p className="text-2xl font-semibold text-gray-900">${(summary.average_budget / 1000).toFixed(0)}K</p>
              </div>
            </div>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search departments..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <button
              onClick={() => setSearchTerm('')}
              className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-md"
            >
              Clear
            </button>
          </div>
        </div>

        {/* Departments Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDepartments.map((dept) => (
            <div key={dept.id} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <div className="h-12 w-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                      <span className="text-indigo-600 font-semibold text-lg">
                        {dept.code}
                      </span>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-lg font-medium text-gray-900">{dept.name}</h3>
                      <p className="text-sm text-gray-500">Code: {dept.code}</p>
                    </div>
                  </div>
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                    {dept.status}
                  </span>
                </div>
                
                <p className="text-sm text-gray-600 mb-4">{dept.description}</p>
                
                <div className="space-y-3 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Employees:</span>
                    <span className="font-medium">{dept.active_employees_count}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Budget:</span>
                    <span className="font-medium">${dept.budget ? (dept.budget / 1000).toFixed(0) + 'K' : 'N/A'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Location:</span>
                    <span className="font-medium">{dept.location || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Remote Work:</span>
                    <span className="font-medium">{dept.allow_remote_work ? 'Allowed' : 'Not Allowed'}</span>
                  </div>
                </div>

                {(dept.contact_email || dept.contact_phone) && (
                  <div className="border-t pt-4">
                    {dept.contact_email && (
                      <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                        <span>📧 {dept.contact_email}</span>
                      </div>
                    )}
                    {dept.contact_phone && (
                      <div className="flex items-center justify-between text-sm text-gray-600">
                        <span>📞 {dept.contact_phone}</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="mt-4 pt-4 border-t flex space-x-2">
                  <button className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded-md text-sm">
                    View Details
                  </button>
                  <button className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded-md text-sm">
                    Edit
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredDepartments.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">🏗️</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No departments found</h3>
            <p className="text-gray-600">Try adjusting your search criteria</p>
          </div>
        )}

        {/* Department Structure */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Organizational Structure</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {departments.map((dept, index) => (
                <div key={dept.id} className="flex items-center">
                  <div className="flex items-center space-x-4">
                    <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                      <span className="text-indigo-600 text-sm font-medium">{index + 1}</span>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="w-32 font-medium text-gray-900">{dept.name}</div>
                        <div className="text-sm text-gray-500">{dept.active_employees_count} employees</div>
                        <div className="text-sm text-gray-500">
                          {dept.budget ? `$${(dept.budget / 1000).toFixed(0)}K budget` : 'No budget set'}
                        </div>
                        <div className="text-sm text-gray-500">{dept.location || 'No location'}</div>
                      </div>
                    </div>
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

export default Departments; 