import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { trainingAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { UserRole } from '../types';

interface Course {
  id: number;
  title: string;
  description: string;
  category: string;
  duration_hours: number;
  instructor_name: string;
  status: string;
  enrollment_count: number;
  completion_rate: number;
  created_at: string;
}

interface Enrollment {
  id: number;
  course_id: number;
  employee_name: string;
  course_title: string;
  enrollment_date: string;
  completion_date: string | null;
  status: string;
  final_score: number;
  grade: string | null;
}

interface Assessment {
  id: number;
  title: string;
  description: string;
  assessment_type: string;
  course_title: string;
  total_points: number;
  passing_score: number;
  duration_minutes: number;
  due_date: string;
  is_active: boolean;
}

interface TrainingSummary {
  total_courses: number;
  active_courses: number;
  total_enrollments: number;
  completed_enrollments: number;
  completion_rate: number;
  total_assessments: number;
  average_score: number;
}

const Training: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('courses');
  
  // Utility function to handle API errors
  const handleApiError = (err: any, defaultMessage: string): string => {
    console.error(`API Error: ${defaultMessage}`, err);
    
    if (err.response?.data?.detail) {
      if (typeof err.response.data.detail === 'string') {
        return err.response.data.detail;
      } else if (Array.isArray(err.response.data.detail)) {
        // Handle Pydantic validation errors
        return err.response.data.detail.map((error: any) => 
          `${error.loc?.join('.') || 'field'}: ${error.msg}`
        ).join(', ');
      } else {
        return JSON.stringify(err.response.data.detail);
      }
    } else if (err.response?.data?.message) {
      return err.response.data.message;
    } else if (err.message) {
      return err.message;
    }
    
    return defaultMessage;
  };
  const [courses, setCourses] = useState<Course[]>([]);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [summary, setSummary] = useState<TrainingSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('All Categories');
  const [selectedStatus, setSelectedStatus] = useState('All Statuses');
  const [selectedEnrollmentStatus, setSelectedEnrollmentStatus] = useState('All Statuses');
  const [showCreateCourse, setShowCreateCourse] = useState(false);
  const [showCreateEnrollment, setShowCreateEnrollment] = useState(false);
  const [showCourseDetails, setShowCourseDetails] = useState(false);
  const [showEditCourse, setShowEditCourse] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [enrollingCourseId, setEnrollingCourseId] = useState<number | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  // Redirect employees away from assessments tab
  useEffect(() => {
    if (user?.role === UserRole.EMPLOYEE && activeTab === 'assessments') {
      setActiveTab('courses');
    }
  }, [user?.role, activeTab]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch summary data
      const summaryResponse = await trainingAPI.getTrainingSummary();
      setSummary(summaryResponse.data);
      
      // Fetch courses
      const coursesResponse = await trainingAPI.getCourses();
      setCourses(coursesResponse.data);
      
      // Fetch enrollments based on user role
      if (user?.role === UserRole.EMPLOYEE) {
        const enrollmentsResponse = await trainingAPI.getMyEnrollments();
        setEnrollments(enrollmentsResponse.data);
      } else {
        const enrollmentsResponse = await trainingAPI.getEnrollments();
        setEnrollments(enrollmentsResponse.data);
      }
      
      // Fetch assessments
      const assessmentsResponse = await trainingAPI.getAssessments();
      setAssessments(assessmentsResponse.data);
      
    } catch (err: any) {
      setError(handleApiError(err, 'Failed to fetch training data'));
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'bg-green-100 text-green-800';
      case 'DRAFT': return 'bg-yellow-100 text-yellow-800';
      case 'ARCHIVED': return 'bg-gray-100 text-gray-800';
      case 'COMPLETED': return 'bg-green-100 text-green-800';
      case 'IN_PROGRESS': return 'bg-blue-100 text-blue-800';
      case 'ENROLLED': return 'bg-blue-100 text-blue-800';
      case 'PENDING': return 'bg-yellow-100 text-yellow-800';
      case 'DROPPED': return 'bg-red-100 text-red-800';
      case 'FAILED': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'Onboarding': return 'bg-blue-100 text-blue-800';
      case 'Leadership': return 'bg-purple-100 text-purple-800';
      case 'Security': return 'bg-red-100 text-red-800';
      case 'Customer Service': return 'bg-green-100 text-green-800';
      case 'Project Management': return 'bg-indigo-100 text-indigo-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredCourses = courses.filter(course => {
    const categoryMatch = selectedCategory === 'All Categories' || course.category === selectedCategory;
    const statusMatch = selectedStatus === 'All Statuses' || course.status === selectedStatus;
    const searchMatch = course.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                       course.description.toLowerCase().includes(searchTerm.toLowerCase());
    return categoryMatch && statusMatch && searchMatch;
  });

  const filteredEnrollments = enrollments.filter(enrollment => {
    const statusMatch = selectedEnrollmentStatus === 'All Statuses' || enrollment.status === selectedEnrollmentStatus;
    const searchMatch = enrollment.employee_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                       enrollment.course_title.toLowerCase().includes(searchTerm.toLowerCase());
    return statusMatch && searchMatch;
  });

  const handleCreateCourse = async (courseData: any) => {
    try {
      // Check if user has permission to create courses
      if (!user?.role || ![UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR].includes(user.role)) {
        setError('You do not have permission to create training courses. Only HR, Organization Admins, and Super Admins can create courses.');
        return;
      }
      
      await trainingAPI.createCourse(courseData);
      setShowCreateCourse(false);
      fetchData(); // Refresh data
    } catch (err: any) {
      setError(handleApiError(err, 'Failed to create course'));
    }
  };

  const handleCreateEnrollment = async (enrollmentData: any) => {
    try {
      await trainingAPI.createEnrollment(enrollmentData);
      setShowCreateEnrollment(false);
      fetchData(); // Refresh data
    } catch (err: any) {
      setError(handleApiError(err, 'Failed to create enrollment'));
    }
  };

  const handleSelfEnroll = async (courseId: number) => {
    try {
      setEnrollingCourseId(courseId);
      await trainingAPI.selfEnroll(courseId);
      fetchData(); // Refresh data
      // Show success message
      const course = courses.find(c => c.id === courseId);
      if (course) {
        alert(`Successfully enrolled in "${course.title}"!`);
      }
    } catch (err: any) {
      setError(handleApiError(err, 'Failed to enroll in course'));
    } finally {
      setEnrollingCourseId(null);
    }
  };

  const handleViewCourseDetails = (course: Course) => {
    setSelectedCourse(course);
    setShowCourseDetails(true);
  };

  const handleEditCourse = (course: Course) => {
    setSelectedCourse(course);
    setShowEditCourse(true);
  };

  const handleUpdateCourse = async (courseData: any) => {
    try {
      if (selectedCourse) {
        await trainingAPI.updateCourse(selectedCourse.id, courseData);
        setShowEditCourse(false);
        setSelectedCourse(null);
        fetchData(); // Refresh data
      }
    } catch (err: any) {
      setError(handleApiError(err, 'Failed to update course'));
    }
  };

  if (loading) {
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
        <div className="text-center py-12">
          <div className="text-red-600 text-6xl mb-4">⚠️</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Training Data</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={fetchData}
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
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Training & Development</h1>
            <p className="text-gray-600">
              {user?.role === UserRole.EMPLOYEE 
                ? 'Browse and enroll in available training courses' 
                : 'Manage training programs and track employee development'
              }
            </p>
          </div>
          <div className="flex space-x-2">
            {user?.role && [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR].includes(user.role) && (
              <>
                <button 
                  onClick={() => setShowCreateCourse(true)}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md"
                >
                  Create New Course
                </button>
                <button 
                  onClick={() => setShowCreateEnrollment(true)}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md"
                >
                  Enroll Employee
                </button>
              </>
            )}
          </div>
        </div>

        {/* Search Bar */}
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search courses, employees, or content..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <button
              onClick={() => setSearchTerm('')}
              className="text-gray-500 hover:text-gray-700"
            >
              Clear
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <span className="text-blue-600 text-xl">🎓</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Courses</p>
                  <p className="text-2xl font-semibold text-gray-900">{summary.total_courses}</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <span className="text-green-600 text-xl">✅</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Active Courses</p>
                  <p className="text-2xl font-semibold text-gray-900">{summary.active_courses}</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <span className="text-purple-600 text-xl">👥</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Enrollments</p>
                  <p className="text-2xl font-semibold text-gray-900">{summary.total_enrollments}</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <span className="text-yellow-600 text-xl">📊</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Completion Rate</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {summary.completion_rate.toFixed(0)}%
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              <button
                onClick={() => setActiveTab('courses')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'courses'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Courses ({courses.length})
              </button>
              <button
                onClick={() => setActiveTab('enrollments')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'enrollments'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {user?.role === UserRole.EMPLOYEE ? 'My Enrollments' : 'Enrollments'} ({enrollments.length})
              </button>
              {user?.role && [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR].includes(user.role) && (
                <button
                  onClick={() => setActiveTab('assessments')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'assessments'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Assessments ({assessments.length})
                </button>
              )}
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'courses' && (
              <div>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Available Courses</h3>
                  <div className="flex space-x-2">
                    <select 
                      className="border border-gray-300 rounded-md px-3 py-1 text-sm"
                      value={selectedCategory}
                      onChange={(e) => setSelectedCategory(e.target.value)}
                    >
                      <option>All Categories</option>
                      <option>Onboarding</option>
                      <option>Leadership</option>
                      <option>Security</option>
                      <option>Customer Service</option>
                      <option>Project Management</option>
                    </select>
                    <select 
                      className="border border-gray-300 rounded-md px-3 py-1 text-sm"
                      value={selectedStatus}
                      onChange={(e) => setSelectedStatus(e.target.value)}
                    >
                      <option>All Statuses</option>
                      <option>ACTIVE</option>
                      <option>DRAFT</option>
                      <option>ARCHIVED</option>
                    </select>
                  </div>
                </div>

                {filteredCourses.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-gray-400 text-6xl mb-4">📚</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Courses Found</h3>
                    <p className="text-gray-600">
                      {searchTerm ? 'No courses match your search criteria' : 'No courses available'}
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredCourses.map((course) => (
                      <div key={course.id} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between mb-4">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getCategoryColor(course.category)}`}>
                            {course.category}
                          </span>
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(course.status)}`}>
                            {course.status}
                          </span>
                        </div>
                        
                        <h3 className="text-lg font-medium text-gray-900 mb-2">{course.title}</h3>
                        <p className="text-sm text-gray-600 mb-4">{course.description}</p>
                        
                        <div className="space-y-2 mb-4">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Duration:</span>
                            <span className="font-medium">{course.duration_hours} hours</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Instructor:</span>
                            <span className="font-medium">{course.instructor_name || 'TBD'}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Enrolled:</span>
                            <span className="font-medium">{course.enrollment_count} students</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Completion Rate:</span>
                            <span className="font-medium">{course.completion_rate.toFixed(0)}%</span>
                          </div>
                        </div>

                        <div className="flex space-x-2">
                          <button 
                            onClick={() => handleViewCourseDetails(course)}
                            className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded-md text-sm"
                          >
                            View Details
                          </button>
                          {user?.role && [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR].includes(user.role) && (
                            <button 
                              onClick={() => handleEditCourse(course)}
                              className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded-md text-sm"
                            >
                              Edit
                            </button>
                          )}
                          {user?.role === UserRole.EMPLOYEE && course.status === 'ACTIVE' && (
                            <button 
                              onClick={() => handleSelfEnroll(course.id)}
                              disabled={enrollingCourseId === course.id || enrollments.some(e => e.course_id === course.id)}
                              className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-3 py-2 rounded-md text-sm"
                            >
                              {enrollingCourseId === course.id ? 'Enrolling...' : 
                               enrollments.some(e => e.course_id === course.id) ? 'Already Enrolled' : 'Enroll'}
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'enrollments' && (
              <div>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    {user?.role === UserRole.EMPLOYEE ? 'My Course Enrollments' : 'Course Enrollments'}
                  </h3>
                  <div className="flex space-x-2">
                    <select 
                      className="border border-gray-300 rounded-md px-3 py-1 text-sm"
                      value={selectedEnrollmentStatus}
                      onChange={(e) => setSelectedEnrollmentStatus(e.target.value)}
                    >
                      <option>All Statuses</option>
                      <option>COMPLETED</option>
                      <option>IN_PROGRESS</option>
                      <option>ENROLLED</option>
                      <option>PENDING</option>
                      <option>DROPPED</option>
                      <option>FAILED</option>
                    </select>
                  </div>
                </div>

                {filteredEnrollments.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-gray-400 text-6xl mb-4">👥</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Enrollments</h3>
                    <p className="text-gray-600">
                      {searchTerm ? 'No enrollments match your search criteria' : 'No enrollments found'}
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Employee
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Course
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Enrollment Date
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Completion Date
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Status
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Grade
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {filteredEnrollments.map((enrollment) => (
                          <tr key={enrollment.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {enrollment.employee_name}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {enrollment.course_title}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {new Date(enrollment.enrollment_date).toLocaleDateString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {enrollment.completion_date ? new Date(enrollment.completion_date).toLocaleDateString() : '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(enrollment.status)}`}>
                                {enrollment.status}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {enrollment.final_score > 0 ? `${enrollment.final_score.toFixed(1)}%` : '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                              <div className="flex space-x-2">
                                <button className="text-indigo-600 hover:text-indigo-900">View</button>
                                {user?.role !== UserRole.EMPLOYEE && (
                                  <button className="text-green-600 hover:text-green-900">Edit</button>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'assessments' && user?.role && [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR].includes(user.role) && (
              <div>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Course Assessments</h3>
                </div>

                {assessments.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-gray-400 text-6xl mb-4">📝</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Assessments</h3>
                    <p className="text-gray-600">No assessments have been created yet</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {assessments.map((assessment) => (
                      <div key={assessment.id} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between mb-4">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            assessment.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {assessment.is_active ? 'Active' : 'Inactive'}
                          </span>
                          <span className="text-xs text-gray-500">{assessment.assessment_type}</span>
                        </div>
                        
                        <h3 className="text-lg font-medium text-gray-900 mb-2">{assessment.title}</h3>
                        <p className="text-sm text-gray-600 mb-2">{assessment.description}</p>
                        <p className="text-sm text-gray-500 mb-4">Course: {assessment.course_title}</p>
                        
                        <div className="space-y-2 mb-4">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Total Points:</span>
                            <span className="font-medium">{assessment.total_points}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Passing Score:</span>
                            <span className="font-medium">{assessment.passing_score}%</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Duration:</span>
                            <span className="font-medium">{assessment.duration_minutes} min</span>
                          </div>
                          {assessment.due_date && (
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-600">Due Date:</span>
                              <span className="font-medium">{new Date(assessment.due_date).toLocaleDateString()}</span>
                            </div>
                          )}
                        </div>

                        <div className="flex space-x-2">
                          <button 
                            onClick={() => console.log('View assessment details:', assessment.id)}
                            className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded-md text-sm"
                          >
                            View Details
                          </button>
                          <button 
                            onClick={() => console.log('Edit assessment:', assessment.id)}
                            className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded-md text-sm"
                          >
                            Edit
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {user?.role !== UserRole.EMPLOYEE && (
            <button className="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-lg text-center transition-colors">
              <div className="text-2xl mb-2">📊</div>
              <div className="font-medium">Training Reports</div>
            </button>
          )}
          <button className="bg-green-600 hover:bg-green-700 text-white p-4 rounded-lg text-center transition-colors">
            <div className="text-2xl mb-2">📈</div>
            <div className="font-medium">Progress Tracking</div>
          </button>
          <button className="bg-purple-600 hover:bg-purple-700 text-white p-4 rounded-lg text-center transition-colors">
            <div className="text-2xl mb-2">🎯</div>
            <div className="font-medium">Skill Assessment</div>
          </button>
        </div>

        {/* Create Course Modal */}
        {showCreateCourse && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Course</h3>
                <form onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.currentTarget);
                  handleCreateCourse({
                    title: formData.get('title'),
                    description: formData.get('description'),
                    category: formData.get('category'),
                    duration_hours: parseFloat(formData.get('duration_hours') as string),
                    course_type: 'ONLINE',
                    status: 'DRAFT'
                  });
                }}>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Title</label>
                      <input
                        type="text"
                        name="title"
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Description</label>
                      <textarea
                        name="description"
                        rows={3}
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Category</label>
                      <select
                        name="category"
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="">Select Category</option>
                        <option value="Onboarding">Onboarding</option>
                        <option value="Leadership">Leadership</option>
                        <option value="Security">Security</option>
                        <option value="Customer Service">Customer Service</option>
                        <option value="Project Management">Project Management</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Duration (hours)</label>
                      <input
                        type="number"
                        name="duration_hours"
                        min="0"
                        step="0.5"
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end space-x-3 mt-6">
                    <button
                      type="button"
                      onClick={() => setShowCreateCourse(false)}
                      className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                    >
                      Create Course
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Create Enrollment Modal */}
        {showCreateEnrollment && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Enroll Employee</h3>
                <form onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.currentTarget);
                  handleCreateEnrollment({
                    course_id: parseInt(formData.get('course_id') as string),
                    employee_id: parseInt(formData.get('employee_id') as string)
                  });
                }}>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Course</label>
                      <select
                        name="course_id"
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="">Select Course</option>
                        {courses.filter(c => c.status === 'ACTIVE').map(course => (
                          <option key={course.id} value={course.id}>{course.title}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Employee ID</label>
                      <input
                        type="number"
                        name="employee_id"
                        required
                        placeholder="Enter employee ID"
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end space-x-3 mt-6">
                    <button
                      type="button"
                      onClick={() => setShowCreateEnrollment(false)}
                      className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                    >
                      Enroll Employee
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Course Details Modal */}
        {showCourseDetails && selectedCourse && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-3/4 max-w-4xl shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Course Details</h3>
                  <button
                    onClick={() => setShowCourseDetails(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">{selectedCourse.title}</h4>
                    <p className="text-sm text-gray-600 mb-4">{selectedCourse.description}</p>
                    
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Category:</span>
                        <span className="text-sm font-medium">{selectedCourse.category}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Duration:</span>
                        <span className="text-sm font-medium">{selectedCourse.duration_hours} hours</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Instructor:</span>
                        <span className="text-sm font-medium">{selectedCourse.instructor_name || 'TBD'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Status:</span>
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(selectedCourse.status)}`}>
                          {selectedCourse.status}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Enrolled Students:</span>
                        <span className="text-sm font-medium">{selectedCourse.enrollment_count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Completion Rate:</span>
                        <span className="text-sm font-medium">{selectedCourse.completion_rate.toFixed(0)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Created:</span>
                        <span className="text-sm font-medium">{new Date(selectedCourse.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h5 className="font-medium text-gray-900 mb-3">Course Statistics</h5>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="space-y-3">
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Completion Progress</span>
                            <span>{selectedCourse.completion_rate.toFixed(0)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-green-600 h-2 rounded-full" 
                              style={{ width: `${selectedCourse.completion_rate}%` }}
                            ></div>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div className="text-center">
                            <div className="text-2xl font-bold text-indigo-600">{selectedCourse.enrollment_count}</div>
                            <div className="text-xs text-gray-600">Enrolled</div>
                          </div>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-green-600">
                              {Math.round(selectedCourse.enrollment_count * selectedCourse.completion_rate / 100)}
                            </div>
                            <div className="text-xs text-gray-600">Completed</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    onClick={() => setShowCourseDetails(false)}
                    className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                  >
                    Close
                  </button>
                  {user?.role !== UserRole.EMPLOYEE && (
                    <button
                      onClick={() => {
                        setShowCourseDetails(false);
                        handleEditCourse(selectedCourse);
                      }}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                    >
                      Edit Course
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Edit Course Modal */}
        {showEditCourse && selectedCourse && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Edit Course</h3>
                  <button
                    onClick={() => setShowEditCourse(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>
                
                <form onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.currentTarget);
                  handleUpdateCourse({
                    title: formData.get('title'),
                    description: formData.get('description'),
                    category: formData.get('category'),
                    duration_hours: parseFloat(formData.get('duration_hours') as string),
                    status: formData.get('status')
                  });
                }}>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Title</label>
                      <input
                        type="text"
                        name="title"
                        defaultValue={selectedCourse.title}
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Description</label>
                      <textarea
                        name="description"
                        defaultValue={selectedCourse.description}
                        rows={3}
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Category</label>
                      <select
                        name="category"
                        defaultValue={selectedCourse.category}
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="Onboarding">Onboarding</option>
                        <option value="Leadership">Leadership</option>
                        <option value="Security">Security</option>
                        <option value="Customer Service">Customer Service</option>
                        <option value="Project Management">Project Management</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Duration (hours)</label>
                      <input
                        type="number"
                        name="duration_hours"
                        defaultValue={selectedCourse.duration_hours}
                        min="0"
                        step="0.5"
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Status</label>
                      <select
                        name="status"
                        defaultValue={selectedCourse.status}
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="DRAFT">Draft</option>
                        <option value="ACTIVE">Active</option>
                        <option value="ARCHIVED">Archived</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex justify-end space-x-3 mt-6">
                    <button
                      type="button"
                      onClick={() => setShowEditCourse(false)}
                      className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                    >
                      Update Course
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Training; 