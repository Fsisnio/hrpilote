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
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedDepartment, setSelectedDepartment] = useState<Department | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

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

  // Department form state
  const [newDepartment, setNewDepartment] = useState({
    name: '',
    code: '',
    description: '',
    budget: '',
    location: '',
    contact_email: '',
    contact_phone: '',
    max_employees: '',
    allow_remote_work: true,
    working_hours_start: '09:00',
    working_hours_end: '17:00'
  });

  const handleCreateDepartment = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newDepartment.name.trim() || !newDepartment.code.trim()) {
      alert('Please fill in the required fields (Name and Code)');
      return;
    }

    try {
      setIsCreating(true);
      
      const departmentData = {
        ...newDepartment,
        budget: newDepartment.budget ? parseInt(newDepartment.budget) : null,
        max_employees: newDepartment.max_employees ? parseInt(newDepartment.max_employees) : null
      };

      await departmentsAPI.createDepartment(departmentData);
      
      // Reset form and close modal
      setNewDepartment({
        name: '',
        code: '',
        description: '',
        budget: '',
        location: '',
        contact_email: '',
        contact_phone: '',
        max_employees: '',
        allow_remote_work: true,
        working_hours_start: '09:00',
        working_hours_end: '17:00'
      });
      setIsAddModalOpen(false);
      
      // Refresh departments list
      await fetchDepartments();
      await fetchSummary();
      
    } catch (err: any) {
      console.error('Error creating department:', err);
      alert(err.response?.data?.detail || 'Failed to create department');
    } finally {
      setIsCreating(false);
    }
  };

  const handleViewDetails = (department: Department) => {
    setSelectedDepartment(department);
    setIsViewModalOpen(true);
  };

  const handleEditDepartment = (department: Department) => {
    setSelectedDepartment(department);
    // Populate edit form with current department data
    setNewDepartment({
      name: department.name,
      code: department.code,
      description: department.description || '',
      budget: department.budget ? department.budget.toString() : '',
      location: department.location || '',
      contact_email: department.contact_email || '',
      contact_phone: department.contact_phone || '',
      max_employees: department.max_employees ? department.max_employees.toString() : '',
      allow_remote_work: department.allow_remote_work,
      working_hours_start: department.working_hours_start || '09:00',
      working_hours_end: department.working_hours_end || '17:00'
    });
    setIsEditModalOpen(true);
  };

  const handleUpdateDepartment = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedDepartment || !newDepartment.name.trim() || !newDepartment.code.trim()) {
      alert('Please fill in the required fields (Name and Code)');
      return;
    }

    try {
      setIsUpdating(true);
      
      const departmentData = {
        ...newDepartment,
        budget: newDepartment.budget ? parseInt(newDepartment.budget) : null,
        max_employees: newDepartment.max_employees ? parseInt(newDepartment.max_employees) : null
      };

      await departmentsAPI.updateDepartment(selectedDepartment.id, departmentData);
      
      // Reset form and close modal
      setSelectedDepartment(null);
      setIsEditModalOpen(false);
      
      // Refresh departments list
      await fetchDepartments();
      await fetchSummary();
      
    } catch (err: any) {
      console.error('Error updating department:', err);
      alert(err.response?.data?.detail || 'Failed to update department');
    } finally {
      setIsUpdating(false);
    }
  };

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
          <button 
            onClick={() => setIsAddModalOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md"
          >
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
                  <button 
                    onClick={() => handleViewDetails(dept)}
                    className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded-md text-sm"
                  >
                    View Details
                  </button>
                  <button 
                    onClick={() => handleEditDepartment(dept)}
                    className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded-md text-sm"
                  >
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

        {/* Add Department Modal */}
        {isAddModalOpen && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Create New Department</h2>
                <button
                  onClick={() => setIsAddModalOpen(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleCreateDepartment} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Department Name *
                    </label>
                    <input
                      type="text"
                      value={newDepartment.name}
                      onChange={(e) => setNewDepartment({...newDepartment, name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      required
                    />
                  </div>

                  {/* Code */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Department Code *
                    </label>
                    <input
                      type="text"
                      value={newDepartment.code}
                      onChange={(e) => setNewDepartment({...newDepartment, code: e.target.value.toUpperCase()})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      required
                    />
                  </div>
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={newDepartment.description}
                    onChange={(e) => setNewDepartment({...newDepartment, description: e.target.value})}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Budget */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Budget ($)
                    </label>
                    <input
                      type="number"
                      value={newDepartment.budget}
                      onChange={(e) => setNewDepartment({...newDepartment, budget: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="e.g., 100000"
                    />
                  </div>

                  {/* Location */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Location
                    </label>
                    <input
                      type="text"
                      value={newDepartment.location}
                      onChange={(e) => setNewDepartment({...newDepartment, location: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Contact Email */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Contact Email
                    </label>
                    <input
                      type="email"
                      value={newDepartment.contact_email}
                      onChange={(e) => setNewDepartment({...newDepartment, contact_email: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>

                  {/* Contact Phone */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Contact Phone
                    </label>
                    <input
                      type="tel"
                      value={newDepartment.contact_phone}
                      onChange={(e) => setNewDepartment({...newDepartment, contact_phone: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Max Employees */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Employees
                    </label>
                    <input
                      type="number"
                      value={newDepartment.max_employees}
                      onChange={(e) => setNewDepartment({...newDepartment, max_employees: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="e.g., 50"
                    />
                  </div>

                  {/* Remote Work */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Allow Remote Work
                    </label>
                    <select
                      value={newDepartment.allow_remote_work ? 'true' : 'false'}
                      onChange={(e) => setNewDepartment({...newDepartment, allow_remote_work: e.target.value === 'true'})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="true">Yes</option>
                      <option value="false">No</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Working Hours Start */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Working Hours Start
                    </label>
                    <input
                      type="time"
                      value={newDepartment.working_hours_start}
                      onChange={(e) => setNewDepartment({...newDepartment, working_hours_start: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>

                  {/* Working Hours End */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Working Hours End
                    </label>
                    <input
                      type="time"
                      value={newDepartment.working_hours_end}
                      onChange={(e) => setNewDepartment({...newDepartment, working_hours_end: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                {/* Form Actions */}
                <div className="flex justify-end space-x-3 pt-4 border-t">
                  <button
                    type="button"
                    onClick={() => setIsAddModalOpen(false)}
                    className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                    disabled={isCreating}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isCreating}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md disabled:opacity-50"
                  >
                    {isCreating ? 'Creating...' : 'Create Department'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* View Department Details Modal */}
        {isViewModalOpen && selectedDepartment && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Department Details</h2>
                <button
                  onClick={() => setIsViewModalOpen(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center space-x-4">
                  <div className="h-16 w-16 bg-indigo-100 rounded-lg flex items-center justify-center">
                    <span className="text-indigo-600 font-semibold text-2xl">
                      {selectedDepartment.code}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900">{selectedDepartment.name}</h3>
                    <span className="inline-flex px-3 py-1 text-sm font-semibold rounded-full bg-green-100 text-green-800">
                      {selectedDepartment.status}
                    </span>
                  </div>
                </div>

                {/* Description */}
                {selectedDepartment.description && (
                  <div>
                    <h4 className="text-lg font-medium text-gray-900 mb-2">Description</h4>
                    <p className="text-gray-600">{selectedDepartment.description}</p>
                  </div>
                )}

                {/* Key Information */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-medium text-gray-500">Department Code</h4>
                      <p className="text-lg text-gray-900">{selectedDepartment.code}</p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-500">Location</h4>
                      <p className="text-lg text-gray-900">{selectedDepartment.location || 'Not specified'}</p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-500">Budget</h4>
                      <p className="text-lg text-gray-900">
                        {selectedDepartment.budget ? `$${(selectedDepartment.budget / 1000).toFixed(0)}K` : 'Not set'}
                      </p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-500">Max Employees</h4>
                      <p className="text-lg text-gray-900">{selectedDepartment.max_employees || 'No limit'}</p>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-medium text-gray-500">Current Employees</h4>
                      <p className="text-lg text-gray-900">{selectedDepartment.active_employees_count}</p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-500">Remote Work</h4>
                      <p className="text-lg text-gray-900">{selectedDepartment.allow_remote_work ? 'Allowed' : 'Not Allowed'}</p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-500">Working Hours</h4>
                      <p className="text-lg text-gray-900">
                        {selectedDepartment.working_hours_start} - {selectedDepartment.working_hours_end}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Contact Information */}
                {(selectedDepartment.contact_email || selectedDepartment.contact_phone) && (
                  <div>
                    <h4 className="text-lg font-medium text-gray-900 mb-3">Contact Information</h4>
                    <div className="space-y-2">
                      {selectedDepartment.contact_email && (
                        <div className="flex items-center space-x-3">
                          <span className="text-gray-500">📧</span>
                          <span className="text-gray-900">{selectedDepartment.contact_email}</span>
                        </div>
                      )}
                      {selectedDepartment.contact_phone && (
                        <div className="flex items-center space-x-3">
                          <span className="text-gray-500">📞</span>
                          <span className="text-gray-900">{selectedDepartment.contact_phone}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex justify-end space-x-3 pt-4 border-t">
                  <button
                    onClick={() => setIsViewModalOpen(false)}
                    className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                  >
                    Close
                  </button>
                  <button
                    onClick={() => {
                      setIsViewModalOpen(false);
                      handleEditDepartment(selectedDepartment);
                    }}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md"
                  >
                    Edit Department
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Edit Department Modal */}
        {isEditModalOpen && selectedDepartment && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Edit Department</h2>
                <button
                  onClick={() => setIsEditModalOpen(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleUpdateDepartment} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Department Name *
                    </label>
                    <input
                      type="text"
                      value={newDepartment.name}
                      onChange={(e) => setNewDepartment({...newDepartment, name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      required
                    />
                  </div>

                  {/* Code */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Department Code *
                    </label>
                    <input
                      type="text"
                      value={newDepartment.code}
                      onChange={(e) => setNewDepartment({...newDepartment, code: e.target.value.toUpperCase()})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      required
                    />
                  </div>
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={newDepartment.description}
                    onChange={(e) => setNewDepartment({...newDepartment, description: e.target.value})}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Budget */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Budget ($)
                    </label>
                    <input
                      type="number"
                      value={newDepartment.budget}
                      onChange={(e) => setNewDepartment({...newDepartment, budget: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="e.g., 100000"
                    />
                  </div>

                  {/* Location */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Location
                    </label>
                    <input
                      type="text"
                      value={newDepartment.location}
                      onChange={(e) => setNewDepartment({...newDepartment, location: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Contact Email */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Contact Email
                    </label>
                    <input
                      type="email"
                      value={newDepartment.contact_email}
                      onChange={(e) => setNewDepartment({...newDepartment, contact_email: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>

                  {/* Contact Phone */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Contact Phone
                    </label>
                    <input
                      type="tel"
                      value={newDepartment.contact_phone}
                      onChange={(e) => setNewDepartment({...newDepartment, contact_phone: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Max Employees */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Employees
                    </label>
                    <input
                      type="number"
                      value={newDepartment.max_employees}
                      onChange={(e) => setNewDepartment({...newDepartment, max_employees: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="e.g., 50"
                    />
                  </div>

                  {/* Remote Work */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Allow Remote Work
                    </label>
                    <select
                      value={newDepartment.allow_remote_work ? 'true' : 'false'}
                      onChange={(e) => setNewDepartment({...newDepartment, allow_remote_work: e.target.value === 'true'})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="true">Yes</option>
                      <option value="false">No</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Working Hours Start */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Working Hours Start
                    </label>
                    <input
                      type="time"
                      value={newDepartment.working_hours_start}
                      onChange={(e) => setNewDepartment({...newDepartment, working_hours_start: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>

                  {/* Working Hours End */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Working Hours End
                    </label>
                    <input
                      type="time"
                      value={newDepartment.working_hours_end}
                      onChange={(e) => setNewDepartment({...newDepartment, working_hours_end: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                {/* Form Actions */}
                <div className="flex justify-end space-x-3 pt-4 border-t">
                  <button
                    type="button"
                    onClick={() => setIsEditModalOpen(false)}
                    className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                    disabled={isUpdating}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isUpdating}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md disabled:opacity-50"
                  >
                    {isUpdating ? 'Updating...' : 'Update Department'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Departments; 