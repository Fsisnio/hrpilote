import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { payrollAPI, employeesAPI } from '../services/api';

interface PayrollSummary {
  total_employees: number;
  total_payroll: number;
  average_salary: number;
  pending_payments: number;
  processed_payments: number;
}

interface PayrollRecord {
  id: number;
  employee: string;
  employee_id: string;
  department: string;
  basic_salary: number;
  allowances: number;
  deductions: number;
  net_salary: number;
  status: string;
  pay_date: string;
  
  // New allocation fields
  housing_allowance: number;
  transport_allowance: number;
  medical_allowance: number;
  meal_allowance: number;
  
  // New deduction fields
  loan_deduction: number;
  advance_deduction: number;
  uniform_deduction: number;
  parking_deduction: number;
  late_penalty: number;
}

interface Employee {
  id: number;
  employee_id: string;
  full_name?: string;
  first_name?: string;
  last_name?: string;
  department?: string;
}

interface PayrollActivity {
  action: string;
  date: string;
  status: string;
}

interface ReportData {
  report_type: string;
  period: string;
  generated_at: string;
  [key: string]: any;
}

const Payroll: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [payrollSummary, setPayrollSummary] = useState<PayrollSummary | null>(null);
  const [payrollRecords, setPayrollRecords] = useState<PayrollRecord[]>([]);
  const [payrollActivity, setPayrollActivity] = useState<PayrollActivity[]>([]);
  const [departments, setDepartments] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [departmentFilter, setDepartmentFilter] = useState<string>('');
  
  // Button states
  const [processingPayroll, setProcessingPayroll] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  
  // Modal states
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportType, setReportType] = useState('summary');
  const [reportMonth, setReportMonth] = useState<number>(new Date().getMonth() + 1);
  const [reportYear, setReportYear] = useState<number>(new Date().getFullYear());
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [showReportData, setShowReportData] = useState(false);
  
  // View and Edit modal states
  const [showViewModal, setShowViewModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<PayrollRecord | null>(null);
  const [editingRecord, setEditingRecord] = useState<PayrollRecord | null>(null);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [newRecord, setNewRecord] = useState({
    employee_id: 0,
    basic_salary: 0,
    status: 'PROCESSING',
    housing_allowance: 0,
    transport_allowance: 0,
    medical_allowance: 0,
    meal_allowance: 0,
    loan_deduction: 0,
    advance_deduction: 0,
    uniform_deduction: 0,
    parking_deduction: 0,
    late_penalty: 0,
    notes: ''
  });
  
  // Payroll Settings states
  const [payrollCycle, setPayrollCycle] = useState('Monthly');
  const [payDay, setPayDay] = useState('Last day of month');
  const [selectedCurrency, setSelectedCurrency] = useState('USD ($)');
  const [settingsSaved, setSettingsSaved] = useState(false);

  useEffect(() => {
    fetchPayrollData();
    fetchPayrollSettings();
  }, []);

  // Normalize numeric input: accept comma as decimal, clamp to >= 0
  const parseAmount = (value: string | number): number => {
    const n = parseFloat(String(value).replace(',', '.'));
    return isNaN(n) ? 0 : Math.max(0, n);
  };

  const fetchPayrollSettings = async () => {
    try {
      const response = await payrollAPI.getPayrollSettings();
      const settings = response.data;
      
      setPayrollCycle(settings.payroll_cycle || 'Monthly');
      setPayDay(settings.pay_day || 'Last day of month');
      setSelectedCurrency(settings.currency || 'USD ($)');
      
      console.log('✅ Payroll settings loaded:', settings);
    } catch (err: any) {
      console.error('❌ Error loading payroll settings:', err);
      // Use default values if loading fails
      setPayrollCycle('Monthly');
      setPayDay('Last day of month');
      setSelectedCurrency('USD ($)');
    }
  };

  const fetchPayrollData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('🔄 Fetching payroll data...');
      
      // Fetch data in parallel
      const [summaryRes, recordsRes, activityRes, departmentsRes, employeesRes] = await Promise.all([
        payrollAPI.getPayrollSummary(),
        payrollAPI.getPayrollRecords(),
        payrollAPI.getPayrollActivity(10),
        payrollAPI.getDepartments(),
        employeesAPI.getEmployees()
      ]);
      
      console.log('📊 API Response:', {
        summary: summaryRes.data,
        records: recordsRes.data,
        activity: activityRes.data,
        departments: departmentsRes.data
      });
      
      setPayrollSummary(summaryRes.data);
      setPayrollRecords(recordsRes.data.records || []);
      setPayrollActivity(activityRes.data || []);
      setDepartments(departmentsRes.data || []);
      // Employees API may return either an array or an object with { employees }
      const employeesData = Array.isArray(employeesRes.data)
        ? employeesRes.data
        : (employeesRes.data?.employees || []);
      setEmployees(employeesData);
      
      console.log('✅ Payroll data loaded successfully');
    } catch (err: any) {
      console.error('❌ Error fetching payroll data:', err);
      console.error('Error details:', {
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data,
        message: err.message
      });
      
      // Provide more specific error messages
      let errorMessage = 'Failed to fetch payroll data';
      if (err.response?.status === 401) {
        errorMessage = 'Authentication failed. Please log out and log back in.';
      } else if (err.response?.status === 403) {
        errorMessage = 'Access denied. You do not have permission to view payroll data.';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      
      setError(errorMessage);
      
      // Set empty data on error to avoid showing stale data
      setPayrollSummary(null);
      setPayrollRecords([]);
      setPayrollActivity([]);
      setDepartments([]);
    } finally {
      setLoading(false);
    }
  };

  const handleProcessPayroll = async () => {
    if (!window.confirm('Are you sure you want to process payroll for all active employees? This action cannot be undone.')) {
      return;
    }
    
    try {
      setProcessingPayroll(true);
      setError(null);
      
      const response = await payrollAPI.processPayroll();
      
      // Check if response has the expected data structure
      if (response.data && response.data.processed_count !== undefined) {
        // Show success message
        alert(`Payroll processed successfully!\n\nProcessed: ${response.data.processed_count} employees\nTotal Gross: $${response.data.total_gross_pay.toLocaleString()}\nTotal Net: $${response.data.total_net_pay.toLocaleString()}`);
        
        // Refresh data
        await fetchPayrollData();
      } else {
        // Handle unexpected response format
        console.warn('Unexpected response format:', response.data);
        await fetchPayrollData();
      }
      
    } catch (err: any) {
      console.error('Error processing payroll:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to process payroll';
      setError(errorMessage);
      
      // Check if it's an "already processed" error
      if (errorMessage.includes('already processed')) {
        alert(`Payroll has already been processed for this month. The data has been refreshed to show current payroll information.`);
        // Refresh data to show existing payroll
        await fetchPayrollData();
      } else {
        alert(`Error processing payroll: ${errorMessage}`);
      }
    } finally {
      setProcessingPayroll(false);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setGeneratingReport(true);
      setError(null);
      
      const response = await payrollAPI.generateReport(reportType, reportMonth, reportYear);
      
      setReportData(response.data);
      setShowReportData(true);
      setShowReportModal(false);
      
    } catch (err: any) {
      console.error('Error generating report:', err);
      setError(err.response?.data?.detail || 'Failed to generate report');
      alert(`Error generating report: ${err.response?.data?.detail || 'Unknown error'}`);
    } finally {
      setGeneratingReport(false);
    }
  };

  const handleViewRecord = (record: PayrollRecord) => {
    setSelectedRecord(record);
    setShowViewModal(true);
  };

  const handleEditRecord = (record: PayrollRecord) => {
    setEditingRecord({ ...record });
    setShowEditModal(true);
  };

  const handleSaveEdit = async () => {
    if (!editingRecord) return;
    
    try {
      console.log('🔄 Starting payroll record update...');
      console.log('📝 Record ID:', editingRecord.id);
      console.log('📊 Record data being sent:', editingRecord);
      
      // Prepare the data to send - only send the fields that the backend expects
      const updateData = {
        basic_salary: editingRecord.basic_salary || 0,
        status: editingRecord.status,
        housing_allowance: editingRecord.housing_allowance || 0,
        transport_allowance: editingRecord.transport_allowance || 0,
        medical_allowance: editingRecord.medical_allowance || 0,
        meal_allowance: editingRecord.meal_allowance || 0,
        loan_deduction: editingRecord.loan_deduction || 0,
        advance_deduction: editingRecord.advance_deduction || 0,
        uniform_deduction: editingRecord.uniform_deduction || 0,
        parking_deduction: editingRecord.parking_deduction || 0,
        late_penalty: editingRecord.late_penalty || 0
      };
      
      console.log('📤 Prepared update data:', updateData);
      
      // Make API call to update the record
      const response = await payrollAPI.updatePayrollRecord(editingRecord.id, updateData);
      
      console.log('✅ API Response received:', response);
      console.log('📋 Response data:', response.data);
      
      // Use the updated record data returned from the backend
      const updatedRecord = response.data.updated_record;
      
      console.log('🔄 Updated record from backend:', updatedRecord);
      
      // Refresh all payroll data to update summary/averages and counts
      await fetchPayrollData();
      console.log('✅ Data refreshed successfully');

      // Show success message
      alert('Payroll record updated successfully!');
      
      // Close modal and reset state
      setShowEditModal(false);
      setEditingRecord(null);
      
    } catch (err: any) {
      console.error('❌ Error updating record:', err);
      console.error('❌ Error response:', err.response);
      console.error('❌ Error data:', err.response?.data);
      
      // Extract proper error message
      let errorMessage = 'An unknown error occurred';

      if (err.response?.status === 422) {
        errorMessage = 'There is an error in your record. All numbers should be positive.';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.response?.data?.message) {
        errorMessage = err.response.data.message;
      } else if (err.response?.data) {
        // Friendly fallback for object/array payloads
        errorMessage = 'There is an error in your record. All numbers should be positive.';
      } else if (err.message) {
        errorMessage = err.message;
      }

      alert(`Error updating record: ${errorMessage}`);
    }
  };

  const handleCancelEdit = () => {
    setShowEditModal(false);
    setEditingRecord(null);
  };

  const handleCreateRecord = () => {
    setNewRecord({
      employee_id: 0,
      basic_salary: 0,
      status: 'PROCESSING',
      housing_allowance: 0,
      transport_allowance: 0,
      medical_allowance: 0,
      meal_allowance: 0,
      loan_deduction: 0,
      advance_deduction: 0,
      uniform_deduction: 0,
      parking_deduction: 0,
      late_penalty: 0,
      notes: ''
    });
    setShowCreateModal(true);
  };

  const handleSaveNewRecord = async () => {
    console.log('🔍 Validating payroll record data:', newRecord);
    
    // Enhanced validation
    if (!newRecord.employee_id || newRecord.employee_id === 0) {
      alert('Please select an employee');
      return;
    }
    
    if (!newRecord.basic_salary || newRecord.basic_salary <= 0) {
      alert('Please enter a valid basic salary (must be greater than 0)');
      return;
    }
    
    // Check for any invalid values
    const invalidFields: string[] = [];
    Object.entries(newRecord).forEach(([key, value]) => {
      if (typeof value === 'number' && (isNaN(value) || value < 0)) {
        invalidFields.push(`${key}: ${value}`);
      }
    });
    
    if (invalidFields.length > 0) {
      alert(`Invalid values detected: ${invalidFields.join(', ')}`);
      return;
    }

    try {
      console.log('🔄 Creating new payroll record...');
      console.log('📝 Record data being sent:', newRecord);
      
      const response = await payrollAPI.createPayrollRecord(newRecord);

      console.log('✅ API Response received:', response);
      console.log('📋 Response data:', response.data);
      
      // Refresh all payroll data so summary and averages update
      await fetchPayrollData();
      console.log('✅ Data refreshed successfully');
      
      // Show success message
      alert('Payroll record created successfully!');
      
      // Close modal and reset state
      setShowCreateModal(false);
      setNewRecord({
        employee_id: 0,
        basic_salary: 0,
        status: 'PROCESSING',
        housing_allowance: 0,
        transport_allowance: 0,
        medical_allowance: 0,
        meal_allowance: 0,
        loan_deduction: 0,
        advance_deduction: 0,
        uniform_deduction: 0,
        parking_deduction: 0,
        late_penalty: 0,
        notes: ''
      });
      
    } catch (err: any) {
      console.error('❌ Error creating record:', err);
      console.error('❌ Error response:', err.response);
      console.error('❌ Error data:', err.response?.data);
      
      // Handle different types of error responses
      let errorMessage = 'Unknown error';
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMessage = err.response.data;
        } else if (err.response.data.detail) {
          errorMessage = err.response.data.detail;
        } else if (err.response.data.message) {
          errorMessage = err.response.data.message;
        } else {
          // Handle validation errors (422)
          if (err.response.status === 422 && err.response.data.detail) {
            errorMessage = Array.isArray(err.response.data.detail) 
              ? err.response.data.detail.map((error: any) => error.msg || error.message).join(', ')
              : err.response.data.detail;
          } else {
            errorMessage = JSON.stringify(err.response.data);
          }
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      alert(`Error creating record: ${errorMessage}`);
    }
  };

  const handleCancelCreate = () => {
    setShowCreateModal(false);
    setNewRecord({
      employee_id: 0,
      basic_salary: 0,
      status: 'PROCESSING',
      housing_allowance: 0,
      transport_allowance: 0,
      medical_allowance: 0,
      meal_allowance: 0,
      loan_deduction: 0,
      advance_deduction: 0,
      uniform_deduction: 0,
      parking_deduction: 0,
      late_penalty: 0,
      notes: ''
    });
  };

  const handleSaveSettings = async () => {
    try {
      console.log('🔄 Saving payroll settings...');
      console.log('📊 Settings to save:', {
        payroll_cycle: payrollCycle,
        pay_day: payDay,
        currency: selectedCurrency
      });
      
      // Make API call to save settings
      const settingsData = {
        payroll_cycle: payrollCycle,
        pay_day: payDay,
        currency: selectedCurrency
      };
      
      const response = await payrollAPI.updatePayrollSettings(settingsData);
      
      console.log('✅ Settings saved successfully:', response.data);
      
      setSettingsSaved(true);
      
      // Show success message
      alert('Payroll settings saved successfully!');
      
      // Reset the saved state after 3 seconds
      setTimeout(() => setSettingsSaved(false), 3000);
      
    } catch (err: any) {
      console.error('❌ Error saving settings:', err);
      
      // Extract proper error message
      let errorMessage = 'An unknown error occurred';
      
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.response?.data?.message) {
        errorMessage = err.response.data.message;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      alert(`Error saving settings: ${errorMessage}`);
    }
  };

  // Utility functions for currency handling
  const getCurrencyCode = (currencyString: string): string => {
    const match = currencyString.match(/^([A-Z]{3})/);
    return match ? match[1] : 'USD';
  };

  const getCurrencySymbol = (currencyString: string): string => {
    const match = currencyString.match(/\(([^)]+)\)/);
    return match ? match[1] : '$';
  };

  const formatCurrency = (amount: number, currencyString: string = selectedCurrency): string => {
    const symbol = getCurrencySymbol(currencyString);
    return `${symbol}${amount.toLocaleString()}`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PAID': return 'bg-green-100 text-green-800';
      case 'PENDING': return 'bg-yellow-100 text-yellow-800';
      case 'PROCESSING': return 'bg-blue-100 text-blue-800';
      case 'DRAFT': return 'bg-gray-100 text-gray-800';
      case 'CANCELLED': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatReportData = (data: ReportData) => {
    if (data.report_type === 'summary') {
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Summary Report - {data.period}</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 p-3 rounded">
              <p className="text-sm text-gray-600">Total Employees</p>
              <p className="text-lg font-semibold">{data.summary.total_employees}</p>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <p className="text-sm text-gray-600">Total Gross Pay</p>
              <p className="text-lg font-semibold">${data.summary.total_gross_pay.toLocaleString()}</p>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <p className="text-sm text-gray-600">Total Net Pay</p>
              <p className="text-lg font-semibold">${data.summary.total_net_pay.toLocaleString()}</p>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <p className="text-sm text-gray-600">Average Salary</p>
              <p className="text-lg font-semibold">${data.summary.average_salary.toLocaleString()}</p>
            </div>
          </div>
        </div>
      );
    } else if (data.report_type === 'detailed') {
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Detailed Report - {data.period}</h3>
          <p className="text-sm text-gray-600">Total Records: {data.total_records}</p>
          <div className="max-h-96 overflow-y-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Department</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Gross Pay</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Net Pay</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.records.map((record: any, index: number) => (
                  <tr key={index}>
                    <td className="px-3 py-2 text-sm">{record.employee_name}</td>
                    <td className="px-3 py-2 text-sm">{record.department}</td>
                    <td className="px-3 py-2 text-sm">${record.gross_pay.toLocaleString()}</td>
                    <td className="px-3 py-2 text-sm">${record.net_pay.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      );
    } else if (data.report_type === 'tax') {
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Tax Report - {data.period}</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 p-3 rounded">
              <p className="text-sm text-gray-600">Total Income Tax</p>
              <p className="text-lg font-semibold">${data.tax_summary.total_income_tax.toLocaleString()}</p>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <p className="text-sm text-gray-600">Total Insurance</p>
              <p className="text-lg font-semibold">${data.tax_summary.total_insurance.toLocaleString()}</p>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <p className="text-sm text-gray-600">Total Pension</p>
              <p className="text-lg font-semibold">${data.tax_summary.total_pension.toLocaleString()}</p>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <p className="text-sm text-gray-600">Total Tax Liability</p>
              <p className="text-lg font-semibold">${data.tax_summary.total_tax_liability.toLocaleString()}</p>
            </div>
          </div>
        </div>
      );
    } else if (data.report_type === 'benefits') {
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Benefits Report - {data.period}</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 p-3 rounded">
              <p className="text-sm text-gray-600">Total Allowances</p>
              <p className="text-lg font-semibold">${data.benefits_summary.total_allowances.toLocaleString()}</p>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <p className="text-sm text-gray-600">Total Bonuses</p>
              <p className="text-lg font-semibold">${data.benefits_summary.total_bonuses.toLocaleString()}</p>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <p className="text-sm text-gray-600">Total Insurance</p>
              <p className="text-lg font-semibold">${data.benefits_summary.total_insurance.toLocaleString()}</p>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <p className="text-sm text-gray-600">Total Benefits</p>
              <p className="text-lg font-semibold">${data.benefits_summary.total_benefits.toLocaleString()}</p>
            </div>
          </div>
        </div>
      );
    }
    
    return <div>Report data not available</div>;
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">Loading payroll data...</div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading payroll data</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
                {error.includes('Authentication failed') ? (
                  <p className="mt-1">Please log out and log back in to refresh your authentication.</p>
                ) : (
                  <p className="mt-1">Please check your authentication and try refreshing the page.</p>
                )}
              </div>
              <div className="mt-4 flex space-x-3">
                <button
                  onClick={fetchPayrollData}
                  className="bg-red-100 hover:bg-red-200 text-red-800 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Retry
                </button>
                {error.includes('Authentication failed') && (
                  <button
                    onClick={() => {
                      localStorage.removeItem('access_token');
                      localStorage.removeItem('refresh_token');
                      window.location.href = '/login';
                    }}
                    className="bg-blue-100 hover:bg-blue-200 text-blue-800 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Logout & Login
                  </button>
                )}
              </div>
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
            <h1 className="text-2xl font-bold text-gray-900">Payroll Management</h1>
            <p className="text-gray-600">Manage employee payroll and compensation</p>
            <div className="flex items-center mt-1">
              <span className="text-sm text-gray-500">Currency: </span>
              <span className="ml-1 text-sm font-medium text-indigo-600">
                {getCurrencyCode(selectedCurrency)} ({getCurrencySymbol(selectedCurrency)})
              </span>
            </div>
          </div>
          <div className="flex space-x-3">
            <button 
              onClick={handleCreateRecord}
              className="px-4 py-2 rounded-md text-white font-medium bg-blue-600 hover:bg-blue-700"
            >
              Create New Record
            </button>
            <button 
              onClick={handleProcessPayroll}
              disabled={processingPayroll}
              className={`px-4 py-2 rounded-md text-white font-medium ${
                processingPayroll 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-green-600 hover:bg-green-700'
              }`}
            >
              {processingPayroll ? 'Processing...' : 'Process Payroll'}
            </button>
            <button 
              onClick={() => setShowReportModal(true)}
              disabled={generatingReport}
              className={`px-4 py-2 rounded-md text-white font-medium ${
                generatingReport 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-indigo-600 hover:bg-indigo-700'
              }`}
            >
              {generatingReport ? 'Generating...' : 'Generate Reports'}
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        {payrollSummary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <span className="text-blue-600 text-xl">👥</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Employees</p>
                  <p className="text-2xl font-semibold text-gray-900">{payrollSummary.total_employees}</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <span className="text-green-600 text-xl">💰</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Payroll</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {formatCurrency(payrollSummary.total_payroll)}
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <span className="text-purple-600 text-xl">📊</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Average Salary</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {formatCurrency(payrollSummary.average_salary)}
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <span className="text-yellow-600 text-xl">⏳</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Pending Payments</p>
                  <p className="text-2xl font-semibold text-gray-900">{payrollSummary.pending_payments}</p>
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
                onClick={() => setActiveTab('overview')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'overview'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Payroll Overview
              </button>
              <button
                onClick={() => setActiveTab('employees')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'employees'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Employee Payroll
              </button>
              <button
                onClick={() => setActiveTab('reports')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'reports'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Reports
              </button>
              <button
                onClick={() => setActiveTab('settings')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'settings'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Settings
              </button>
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Payroll Chart Placeholder */}
                <div className="bg-gray-50 p-8 rounded-lg text-center">
                  <div className="text-gray-400 text-4xl mb-4">📈</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Payroll Trends</h3>
                  <p className="text-gray-600">Payroll analytics and charts will be displayed here</p>
                </div>

                {/* Recent Payroll Activity */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Payroll Activity</h3>
                  <div className="space-y-3">
                    {payrollActivity.length > 0 ? (
                      payrollActivity.map((activity, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div>
                            <p className="text-sm font-medium text-gray-900">{activity.action}</p>
                            <p className="text-xs text-gray-500">{activity.date}</p>
                          </div>
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            activity.status === 'PAID' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {activity.status}
                          </span>
                        </div>
                      ))
                    ) : (
                      <div className="text-center text-gray-500 py-8">
                        No recent payroll activity
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'employees' && (
              <div>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Employee Payroll</h3>
                  <div className="flex space-x-2">
                    <select 
                      className="border border-gray-300 rounded-md px-3 py-1 text-sm"
                      value={departmentFilter}
                      onChange={(e) => setDepartmentFilter(e.target.value)}
                    >
                      <option value="">All Departments</option>
                      {departments.map((dept) => (
                        <option key={dept} value={dept}>{dept}</option>
                      ))}
                    </select>
                    <select 
                      className="border border-gray-300 rounded-md px-3 py-1 text-sm"
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                    >
                      <option value="">All Statuses</option>
                      <option value="PAID">Paid</option>
                      <option value="PENDING">Pending</option>
                      <option value="PROCESSING">Processing</option>
                      <option value="DRAFT">Draft</option>
                    </select>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Employee
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Department
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Basic Salary
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Allowances
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Deductions
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Net Salary
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {payrollRecords.length > 0 ? (
                        payrollRecords
                          .filter(record => !departmentFilter || record.department === departmentFilter)
                          .filter(record => !statusFilter || record.status === statusFilter)
                          .map((employee) => (
                          <tr key={employee.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">{employee.employee}</div>
                              <div className="text-sm text-gray-500">{employee.employee_id}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {employee.department}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatCurrency(employee.basic_salary)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatCurrency(employee.allowances)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatCurrency(employee.deductions)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {formatCurrency(employee.net_salary)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(employee.status)}`}>
                                {employee.status}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                              <div className="flex space-x-2">
                                <button 
                                  onClick={() => handleViewRecord(employee)}
                                  className="text-indigo-600 hover:text-indigo-900 hover:underline"
                                >
                                  View
                                </button>
                                <button 
                                  onClick={() => handleEditRecord(employee)}
                                  className="text-green-600 hover:text-green-900 hover:underline"
                                >
                                  Edit
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={8} className="px-6 py-8 text-center text-gray-500">
                            No payroll records found
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'reports' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <h4 className="font-medium text-gray-900 mb-4">Generate Reports</h4>
                    <div className="space-y-3">
                      <button 
                        onClick={() => {
                          setReportType('summary');
                          setShowReportModal(true);
                        }}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md"
                      >
                        Payroll Summary Report
                      </button>
                      <button 
                        onClick={() => {
                          setReportType('tax');
                          setShowReportModal(true);
                        }}
                        className="w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md"
                      >
                        Tax Report
                      </button>
                      <button 
                        onClick={() => {
                          setReportType('benefits');
                          setShowReportModal(true);
                        }}
                        className="w-full bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md"
                      >
                        Benefits Report
                      </button>
                      <button 
                        onClick={() => {
                          setReportType('detailed');
                          setShowReportModal(true);
                        }}
                        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md"
                      >
                        Detailed Report
                      </button>
                    </div>
                  </div>
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <h4 className="font-medium text-gray-900 mb-4">Recent Reports</h4>
                    <div className="space-y-2">
                      {[
                        'Payroll Summary - January 2024.pdf',
                        'Tax Report - Q4 2023.pdf',
                        'Benefits Summary - December 2023.pdf'
                      ].map((report, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-white rounded">
                          <span className="text-sm text-gray-700">{report}</span>
                          <button className="text-indigo-600 hover:text-indigo-900 text-sm">Download</button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'settings' && (
              <div className="space-y-6">
                <div className="bg-gray-50 p-6 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-4">Payroll Settings</h4>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Payroll Cycle</label>
                      <select 
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={payrollCycle}
                        onChange={(e) => setPayrollCycle(e.target.value)}
                      >
                        <option value="Monthly">Monthly</option>
                        <option value="Bi-weekly">Bi-weekly</option>
                        <option value="Weekly">Weekly</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Pay Day</label>
                      <select 
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={payDay}
                        onChange={(e) => setPayDay(e.target.value)}
                      >
                        <option value="Last day of month">Last day of month</option>
                        <option value="15th of month">15th of month</option>
                        <option value="1st of month">1st of month</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Currency</label>
                      <select 
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={selectedCurrency}
                        onChange={(e) => setSelectedCurrency(e.target.value)}
                      >
                        {/* Major Global Currencies */}
                        <optgroup label="Global Currencies">
                          <option value="USD ($)">USD ($)</option>
                          <option value="EUR (€)">EUR (€)</option>
                          <option value="GBP (£)">GBP (£)</option>
                        </optgroup>
                        
                        {/* African Currencies */}
                        <optgroup label="African Currencies">
                          {/* North Africa */}
                          <option value="EGP (E£) - Egyptian Pound">EGP (E£) - Egyptian Pound</option>
                          <option value="MAD (د.م.) - Moroccan Dirham">MAD (د.م.) - Moroccan Dirham</option>
                          <option value="TND (د.ت) - Tunisian Dinar">TND (د.ت) - Tunisian Dinar</option>
                          <option value="LYD (ل.د) - Libyan Dinar">LYD (ل.د) - Libyan Dinar</option>
                          <option value="DZD (د.ج) - Algerian Dinar">DZD (د.ج) - Algerian Dinar</option>
                          
                          {/* West Africa */}
                          <option value="NGN (₦) - Nigerian Naira">NGN (₦) - Nigerian Naira</option>
                          <option value="GHS (₵) - Ghanaian Cedi">GHS (₵) - Ghanaian Cedi</option>
                          <option value="XOF (CFA) - West African CFA Franc">XOF (CFA) - West African CFA Franc</option>
                          <option value="XAF (FCFA) - Central African CFA Franc">XAF (FCFA) - Central African CFA Franc</option>
                          <option value="GMD (D) - Gambian Dalasi">GMD (D) - Gambian Dalasi</option>
                          <option value="MUR (₨) - Mauritian Rupee">MUR (₨) - Mauritian Rupee</option>
                          
                          {/* East Africa */}
                          <option value="KES (KSh) - Kenyan Shilling">KES (KSh) - Kenyan Shilling</option>
                          <option value="UGX (USh) - Ugandan Shilling">UGX (USh) - Ugandan Shilling</option>
                          <option value="TZS (TSh) - Tanzanian Shilling">TZS (TSh) - Tanzanian Shilling</option>
                          <option value="ETB (Br) - Ethiopian Birr">ETB (Br) - Ethiopian Birr</option>
                          <option value="RWF (FRw) - Rwandan Franc">RWF (FRw) - Rwandan Franc</option>
                          <option value="BIF (FBu) - Burundian Franc">BIF (FBu) - Burundian Franc</option>
                          
                          {/* Southern Africa */}
                          <option value="ZAR (R) - South African Rand">ZAR (R) - South African Rand</option>
                          <option value="BWP (P) - Botswana Pula">BWP (P) - Botswana Pula</option>
                          <option value="NAD (N$) - Namibian Dollar">NAD (N$) - Namibian Dollar</option>
                          <option value="ZMW (ZK) - Zambian Kwacha">ZMW (ZK) - Zambian Kwacha</option>
                          <option value="MWK (MK) - Malawian Kwacha">MWK (MK) - Malawian Kwacha</option>
                          <option value="MZN (MT) - Mozambican Metical">MZN (MT) - Mozambican Metical</option>
                          
                          {/* Central Africa */}
                          <option value="CDF (FC) - Congolese Franc">CDF (FC) - Congolese Franc</option>
                          <option value="XAF (FCFA) - Central African CFA Franc">XAF (FCFA) - Central African CFA Franc</option>
                          <option value="STD (Db) - São Tomé and Príncipe Dobra">STD (Db) - São Tomé and Príncipe Dobra</option>
                          
                          {/* Other African Countries */}
                          <option value="SDG (ج.س) - Sudanese Pound">SDG (ج.س) - Sudanese Pound</option>
                          <option value="SSP (SSP) - South Sudanese Pound">SSP (SSP) - South Sudanese Pound</option>
                          <option value="DJF (Fdj) - Djiboutian Franc">DJF (Fdj) - Djiboutian Franc</option>
                          <option value="SOS (S) - Somali Shilling">SOS (S) - Somali Shilling</option>
                          <option value="KMF (CF) - Comorian Franc">KMF (CF) - Comorian Franc</option>
                          <option value="SCR (₨) - Seychellois Rupee">SCR (₨) - Seychellois Rupee</option>
                        </optgroup>
                      </select>
                    </div>
                    <div className="flex items-center justify-between">
                      <button 
                        onClick={handleSaveSettings}
                        className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md"
                      >
                        Save Settings
                      </button>
                      {settingsSaved && (
                        <span className="text-green-600 text-sm font-medium">
                          ✓ Settings saved successfully!
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Report Generation Modal */}
        {showReportModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Generate Payroll Report</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Report Type</label>
                    <select 
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      value={reportType}
                      onChange={(e) => setReportType(e.target.value)}
                    >
                      <option value="summary">Summary Report</option>
                      <option value="detailed">Detailed Report</option>
                      <option value="tax">Tax Report</option>
                      <option value="benefits">Benefits Report</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Month</label>
                    <select 
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      value={reportMonth}
                      onChange={(e) => setReportMonth(Number(e.target.value))}
                    >
                      {Array.from({length: 12}, (_, i) => i + 1).map(month => (
                        <option key={month} value={month}>
                          {new Date(2024, month - 1).toLocaleString('default', { month: 'long' })}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Year</label>
                    <select 
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      value={reportYear}
                      onChange={(e) => setReportYear(Number(e.target.value))}
                    >
                      {Array.from({length: 5}, (_, i) => new Date().getFullYear() - 2 + i).map(year => (
                        <option key={year} value={year}>{year}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="flex space-x-3 mt-6">
                  <button
                    onClick={handleGenerateReport}
                    disabled={generatingReport}
                    className={`flex-1 px-4 py-2 rounded-md text-white font-medium ${
                      generatingReport 
                        ? 'bg-gray-400 cursor-not-allowed' 
                        : 'bg-indigo-600 hover:bg-indigo-700'
                    }`}
                  >
                    {generatingReport ? 'Generating...' : 'Generate Report'}
                  </button>
                  <button
                    onClick={() => setShowReportModal(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Report Data Display Modal */}
        {showReportData && reportData && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-10 mx-auto p-5 border w-4/5 max-w-4xl shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Generated Report</h3>
                  <button
                    onClick={() => setShowReportData(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <span className="text-2xl">×</span>
                  </button>
                </div>
                <div className="mb-4">
                  <p className="text-sm text-gray-600">
                    Generated on: {new Date(reportData.generated_at).toLocaleString()}
                  </p>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {formatReportData(reportData)}
                </div>
                <div className="mt-6 flex justify-end space-x-3">
                  <button
                    onClick={async () => {
                      try {
                        const response = await payrollAPI.downloadPDF(reportData.report_type, reportMonth, reportYear);
                        
                        // Create blob and download
                        const blob = new Blob([response.data], { type: 'application/pdf' });
                        const url = window.URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.href = url;
                        
                        // Create filename
                        const monthName = new Date(reportYear, reportMonth - 1).toLocaleString('default', { month: 'long' });
                        link.download = `payroll_${reportData.report_type}_report_${monthName}_${reportYear}.pdf`;
                        
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        window.URL.revokeObjectURL(url);
                        
                        // Show success message
                        alert('PDF downloaded successfully!');
                      } catch (error: any) {
                        console.error('Error downloading PDF:', error);
                        alert(`Error downloading PDF: ${error.response?.data?.detail || 'Unknown error'}`);
                      }
                    }}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md"
                  >
                    Download PDF
                  </button>
                  <button
                    onClick={() => setShowReportData(false)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* View Record Modal */}
        {showViewModal && selectedRecord && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-10 mx-auto p-5 border w-4/5 max-w-2xl shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Payroll Record Details</h3>
                  <button
                    onClick={() => setShowViewModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <span className="text-2xl">×</span>
                  </button>
                </div>
                
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Employee</label>
                      <p className="text-sm text-gray-900">{selectedRecord.employee}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Employee ID</label>
                      <p className="text-sm text-gray-900">{selectedRecord.employee_id}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Department</label>
                      <p className="text-sm text-gray-900">{selectedRecord.department}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Status</label>
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(selectedRecord.status)}`}>
                        {selectedRecord.status}
                      </span>
                    </div>
                  </div>
                  
                  <div className="border-t pt-4">
                    <h4 className="font-medium text-gray-900 mb-3">Salary Breakdown</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Basic Salary</label>
                        <p className="text-lg font-semibold text-gray-900">${selectedRecord.basic_salary.toLocaleString()}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Allowances</label>
                        <p className="text-lg font-semibold text-gray-900">${selectedRecord.allowances.toLocaleString()}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Deductions</label>
                        <p className="text-lg font-semibold text-gray-900">${selectedRecord.deductions.toLocaleString()}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Net Salary</label>
                        <p className="text-lg font-semibold text-green-600">${selectedRecord.net_salary.toLocaleString()}</p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="mt-6 flex justify-end">
                  <button
                    onClick={() => setShowViewModal(false)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Edit Record Modal */}
        {showEditModal && editingRecord && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-10 mx-auto p-5 border w-4/5 max-w-2xl shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Edit Payroll Record</h3>
                  <button
                    onClick={handleCancelEdit}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <span className="text-2xl">×</span>
                  </button>
                </div>
                
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Employee</label>
                      <p className="text-sm text-gray-900">{editingRecord.employee}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Employee ID</label>
                      <p className="text-sm text-gray-900">{editingRecord.employee_id}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Department</label>
                      <p className="text-sm text-gray-900">{editingRecord.department}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Status</label>
                      <select
                        value={editingRecord.status}
                        onChange={(e) => setEditingRecord({...editingRecord, status: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      >
                        <option value="PAID">Paid</option>
                        <option value="PENDING">Pending</option>
                        <option value="PROCESSING">Processing</option>
                        <option value="DRAFT">Draft</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="border-t pt-4">
                    <h4 className="font-medium text-gray-900 mb-3">Salary Breakdown</h4>
                    
                    {/* Basic Salary */}
                    <div className="mb-4">
                      <label className="block text-sm font-medium text-gray-700 mb-2">Basic Salary</label>
                      <input
                        type="number"
                        value={editingRecord.basic_salary}
                        onChange={(e) => setEditingRecord({...editingRecord, basic_salary: parseAmount(e.target.value)})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        step="0.01"
                        min="0"
                      />
                    </div>

                    {/* Allocations Section */}
                    <div className="mb-4">
                      <h5 className="text-sm font-medium text-gray-700 mb-3">Allocations</h5>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Housing Allowance</label>
                          <input
                            type="number"
                            value={editingRecord.housing_allowance || 0}
                            onChange={(e) => setEditingRecord({...editingRecord, housing_allowance: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Transport Allowance</label>
                          <input
                            type="number"
                            value={editingRecord.transport_allowance || 0}
                            onChange={(e) => setEditingRecord({...editingRecord, transport_allowance: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Medical Allowance</label>
                          <input
                            type="number"
                            value={editingRecord.medical_allowance || 0}
                            onChange={(e) => setEditingRecord({...editingRecord, medical_allowance: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Meal Allowance</label>
                          <input
                            type="number"
                            value={editingRecord.meal_allowance || 0}
                            onChange={(e) => setEditingRecord({...editingRecord, meal_allowance: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Deductions Section */}
                    <div className="mb-4">
                      <h5 className="text-sm font-medium text-gray-700 mb-3">Deductions</h5>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Loan Deduction</label>
                          <input
                            type="number"
                            value={editingRecord.loan_deduction || 0}
                            onChange={(e) => setEditingRecord({...editingRecord, loan_deduction: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Advance Deduction</label>
                          <input
                            type="number"
                            value={editingRecord.advance_deduction || 0}
                            onChange={(e) => setEditingRecord({...editingRecord, advance_deduction: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Uniform Deduction</label>
                          <input
                            type="number"
                            value={editingRecord.uniform_deduction || 0}
                            onChange={(e) => setEditingRecord({...editingRecord, uniform_deduction: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Parking Deduction</label>
                          <input
                            type="number"
                            value={editingRecord.parking_deduction || 0}
                            onChange={(e) => setEditingRecord({...editingRecord, parking_deduction: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Late Penalty</label>
                          <input
                            type="number"
                            value={editingRecord.late_penalty || 0}
                            onChange={(e) => setEditingRecord({...editingRecord, late_penalty: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Net Salary Calculation */}
                    <div className="bg-gray-50 p-4 rounded-md">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-gray-700">Net Salary</span>
                        <span className="text-lg font-semibold text-green-600">
                          ${(() => {
                            const totalAllocations = (editingRecord.housing_allowance || 0) + 
                                                    (editingRecord.transport_allowance || 0) + 
                                                    (editingRecord.medical_allowance || 0) + 
                                                    (editingRecord.meal_allowance || 0);
                            const totalDeductions = (editingRecord.loan_deduction || 0) + 
                                                  (editingRecord.advance_deduction || 0) + 
                                                  (editingRecord.uniform_deduction || 0) + 
                                                  (editingRecord.parking_deduction || 0) + 
                                                  (editingRecord.late_penalty || 0);
                            return ((editingRecord.basic_salary + totalAllocations) - totalDeductions).toLocaleString();
                          })()}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="mt-6 flex justify-end space-x-3">
                  <button
                    onClick={handleSaveEdit}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md"
                  >
                    Save Changes
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Create New Record Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-10 mx-auto p-5 border w-4/5 max-w-2xl shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Create New Payroll Record</h3>
                  <button
                    onClick={handleCancelCreate}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <span className="text-2xl">×</span>
                  </button>
                </div>
                
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Employee *</label>
                      <select
                        value={newRecord.employee_id}
                        onChange={(e) => setNewRecord({...newRecord, employee_id: parseInt(e.target.value)})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        required
                      >
                        <option value={0}>Select Employee</option>
                        {employees.map((employee) => {
                          const displayName = employee.full_name && employee.full_name.trim().length > 0
                            ? employee.full_name
                            : `${employee.first_name || ''} ${employee.last_name || ''}`.trim() || employee.employee_id;
                          return (
                            <option key={employee.id} value={employee.id}>
                              {displayName} ({employee.employee_id})
                            </option>
                          );
                        })}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                      <select
                        value={newRecord.status}
                        onChange={(e) => setNewRecord({...newRecord, status: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      >
                        <option value="DRAFT">Draft</option>
                        <option value="PROCESSING">Processing</option>
                        <option value="APPROVED">Approved</option>
                        <option value="PAID">Paid</option>
                        <option value="CANCELLED">Cancelled</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="border-t pt-4">
                    <h4 className="font-medium text-gray-900 mb-3">Salary Breakdown</h4>
                    
                    {/* Basic Salary */}
                    <div className="mb-4">
                      <label className="block text-sm font-medium text-gray-700 mb-2">Basic Salary *</label>
                      <input
                        type="number"
                        value={newRecord.basic_salary}
                        onChange={(e) => setNewRecord({...newRecord, basic_salary: parseAmount(e.target.value)})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        step="0.01"
                        min="0"
                        required
                      />
                    </div>

                    {/* Allocations Section */}
                    <div className="mb-4">
                      <h5 className="text-sm font-medium text-gray-700 mb-3">Allocations</h5>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Housing Allowance</label>
                          <input
                            type="number"
                            value={newRecord.housing_allowance}
                            onChange={(e) => setNewRecord({...newRecord, housing_allowance: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Transport Allowance</label>
                          <input
                            type="number"
                            value={newRecord.transport_allowance}
                            onChange={(e) => setNewRecord({...newRecord, transport_allowance: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Medical Allowance</label>
                          <input
                            type="number"
                            value={newRecord.medical_allowance}
                            onChange={(e) => setNewRecord({...newRecord, medical_allowance: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Meal Allowance</label>
                          <input
                            type="number"
                            value={newRecord.meal_allowance}
                            onChange={(e) => setNewRecord({...newRecord, meal_allowance: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Deductions Section */}
                    <div className="mb-4">
                      <h5 className="text-sm font-medium text-gray-700 mb-3">Deductions</h5>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Loan Deduction</label>
                          <input
                            type="number"
                            value={newRecord.loan_deduction}
                            onChange={(e) => setNewRecord({...newRecord, loan_deduction: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Advance Deduction</label>
                          <input
                            type="number"
                            value={newRecord.advance_deduction}
                            onChange={(e) => setNewRecord({...newRecord, advance_deduction: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Uniform Deduction</label>
                          <input
                            type="number"
                            value={newRecord.uniform_deduction}
                            onChange={(e) => setNewRecord({...newRecord, uniform_deduction: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Parking Deduction</label>
                          <input
                            type="number"
                            value={newRecord.parking_deduction}
                            onChange={(e) => setNewRecord({...newRecord, parking_deduction: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Late Penalty</label>
                          <input
                            type="number"
                            value={newRecord.late_penalty}
                            onChange={(e) => setNewRecord({...newRecord, late_penalty: parseAmount(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            step="0.01"
                            min="0"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Notes */}
                    <div className="mb-4">
                      <label className="block text-sm font-medium text-gray-700 mb-2">Notes</label>
                      <textarea
                        value={newRecord.notes}
                        onChange={(e) => setNewRecord({...newRecord, notes: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        rows={3}
                        placeholder="Additional notes (optional)"
                      />
                    </div>

                    {/* Net Salary Calculation */}
                    <div className="bg-gray-50 p-4 rounded-md">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-gray-700">Net Salary</span>
                        <span className="text-lg font-semibold text-green-600">
                          ${(() => {
                            const totalAllocations = newRecord.housing_allowance + 
                                                    newRecord.transport_allowance + 
                                                    newRecord.medical_allowance + 
                                                    newRecord.meal_allowance;
                            const totalDeductions = newRecord.loan_deduction + 
                                                  newRecord.advance_deduction + 
                                                  newRecord.uniform_deduction + 
                                                  newRecord.parking_deduction + 
                                                  newRecord.late_penalty;
                            return ((newRecord.basic_salary + totalAllocations) - totalDeductions).toLocaleString();
                          })()}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="mt-6 flex justify-end space-x-3">
                  <button
                    onClick={handleSaveNewRecord}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md"
                  >
                    Create Record
                  </button>
                  <button
                    onClick={handleCancelCreate}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Payroll; 