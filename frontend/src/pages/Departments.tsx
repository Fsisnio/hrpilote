import React, { useState } from 'react';
import Layout from '../components/Layout';

const Departments: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const departments = [
    {
      id: 1,
      name: 'Engineering',
      code: 'ENG',
      description: 'Software development and technical operations',
      status: 'ACTIVE',
      employeeCount: 45,
      budget: 2500000,
      location: 'Building A, Floor 3',
      manager: 'Sarah Johnson',
      contactEmail: 'engineering@company.com',
      contactPhone: '+1-555-0123'
    },
    {
      id: 2,
      name: 'Marketing',
      code: 'MKT',
      description: 'Brand management and digital marketing',
      status: 'ACTIVE',
      employeeCount: 28,
      budget: 1800000,
      location: 'Building B, Floor 2',
      manager: 'Michael Chen',
      contactEmail: 'marketing@company.com',
      contactPhone: '+1-555-0124'
    },
    {
      id: 3,
      name: 'Sales',
      code: 'SLS',
      description: 'Customer acquisition and revenue generation',
      status: 'ACTIVE',
      employeeCount: 35,
      budget: 2200000,
      location: 'Building A, Floor 1',
      manager: 'Emily Rodriguez',
      contactEmail: 'sales@company.com',
      contactPhone: '+1-555-0125'
    },
    {
      id: 4,
      name: 'Human Resources',
      code: 'HR',
      description: 'Employee relations and talent management',
      status: 'ACTIVE',
      employeeCount: 12,
      budget: 800000,
      location: 'Building C, Floor 1',
      manager: 'David Thompson',
      contactEmail: 'hr@company.com',
      contactPhone: '+1-555-0126'
    },
    {
      id: 5,
      name: 'Finance',
      code: 'FIN',
      description: 'Financial planning and accounting',
      status: 'ACTIVE',
      employeeCount: 18,
      budget: 1200000,
      location: 'Building C, Floor 2',
      manager: 'Lisa Wang',
      contactEmail: 'finance@company.com',
      contactPhone: '+1-555-0127'
    },
    {
      id: 6,
      name: 'Operations',
      code: 'OPS',
      description: 'Business operations and process improvement',
      status: 'ACTIVE',
      employeeCount: 22,
      budget: 1500000,
      location: 'Building B, Floor 1',
      manager: 'Robert Kim',
      contactEmail: 'operations@company.com',
      contactPhone: '+1-555-0128'
    }
  ];

  const filteredDepartments = departments.filter(dept =>
    dept.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    dept.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    dept.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalEmployees = departments.reduce((sum, dept) => sum + dept.employeeCount, 0);
  const totalBudget = departments.reduce((sum, dept) => sum + dept.budget, 0);
  const averageBudget = totalBudget / departments.length;

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
                <p className="text-2xl font-semibold text-gray-900">{departments.length}</p>
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
                <p className="text-2xl font-semibold text-gray-900">{totalEmployees}</p>
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
                <p className="text-2xl font-semibold text-gray-900">${(totalBudget / 1000000).toFixed(1)}M</p>
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
                <p className="text-2xl font-semibold text-gray-900">${(averageBudget / 1000).toFixed(0)}K</p>
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
                    <span className="font-medium">{dept.employeeCount}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Budget:</span>
                    <span className="font-medium">${(dept.budget / 1000).toFixed(0)}K</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Manager:</span>
                    <span className="font-medium">{dept.manager}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Location:</span>
                    <span className="font-medium">{dept.location}</span>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                    <span>📧 {dept.contactEmail}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>📞 {dept.contactPhone}</span>
                  </div>
                </div>

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
                        <div className="text-sm text-gray-500">{dept.manager}</div>
                        <div className="text-sm text-gray-500">{dept.employeeCount} employees</div>
                        <div className="text-sm text-gray-500">${(dept.budget / 1000).toFixed(0)}K budget</div>
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