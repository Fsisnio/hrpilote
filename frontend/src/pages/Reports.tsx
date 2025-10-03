import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { reportsAPI } from '../services/api';

const Reports: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCustomReportModal, setShowCustomReportModal] = useState(false);
  const [showGenerateReportModal, setShowGenerateReportModal] = useState(false);
  const [selectedReport, setSelectedReport] = useState<any>(null);
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [employeeGrowthData, setEmployeeGrowthData] = useState<any[]>([]);
  const [departmentData, setDepartmentData] = useState<any[]>([]);

  const reportCategories = [
    {
      name: 'Employee Reports',
      icon: '👥',
      reports: [
        { name: 'Employee Directory', description: 'Complete list of all employees' },
        { name: 'Employee Turnover', description: 'Analysis of employee retention' },
        { name: 'Performance Reviews', description: 'Employee performance metrics' },
        { name: 'Training Completion', description: 'Training and development progress' }
      ]
    },
    {
      name: 'Attendance Reports',
      icon: '⏰',
      reports: [
        { name: 'Attendance Summary', description: 'Daily attendance overview' },
        { name: 'Late Arrivals', description: 'Employees with frequent late arrivals' },
        { name: 'Overtime Analysis', description: 'Overtime hours and costs' },
        { name: 'Leave Balance', description: 'Employee leave balances' }
      ]
    },
    {
      name: 'Payroll Reports',
      icon: '💰',
      reports: [
        { name: 'Payroll Summary', description: 'Monthly payroll overview' },
        { name: 'Tax Reports', description: 'Tax deductions and filings' },
        { name: 'Benefits Summary', description: 'Employee benefits analysis' },
        { name: 'Salary Distribution', description: 'Salary ranges and distribution' }
      ]
    },
    {
      name: 'Recruitment Reports',
      icon: '🎯',
      reports: [
        { name: 'Hiring Pipeline', description: 'Current recruitment status' },
        { name: 'Time to Hire', description: 'Average time to fill positions' },
        { name: 'Source Analysis', description: 'Effectiveness of recruitment sources' },
        { name: 'Cost per Hire', description: 'Recruitment cost analysis' }
      ]
    }
  ];

  const recentReports = [
    { name: 'Employee Directory - January 2024', date: '2024-01-31', type: 'PDF', size: '2.3 MB' },
    { name: 'Payroll Summary - December 2023', date: '2024-01-01', type: 'Excel', size: '1.8 MB' },
    { name: 'Attendance Report - Q4 2023', date: '2023-12-31', type: 'PDF', size: '3.1 MB' },
    { name: 'Training Completion Report', date: '2023-12-28', type: 'Excel', size: '1.2 MB' }
  ];

  // Initialize analytics data
  const defaultAnalyticsData = {
    totalEmployees: 150,
    activeEmployees: 142,
    newHires: 8,
    turnoverRate: 5.3,
    averageSalary: 5200,
    totalPayroll: 780000,
    averageAttendance: 95.2,
    pendingLeaveRequests: 12
  };

  useEffect(() => {
    const fetchReportsData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch dashboard data from API
        const dashboardResponse = await reportsAPI.getDashboardData();
        const dashboardData = dashboardResponse.data;
        
        // Set analytics data from API response
        setAnalyticsData({
          totalEmployees: dashboardData.employee_count || 0,
          activeEmployees: dashboardData.active_employees || 0,
          newHires: dashboardData.new_hires || 0,
          turnoverRate: dashboardData.turnover_rate || 0,
          averageSalary: dashboardData.average_salary || 0,
          totalPayroll: dashboardData.total_payroll || 0,
          averageAttendance: dashboardData.attendance_rate || 0,
          pendingLeaveRequests: dashboardData.pending_leave_requests || 0
        });
        
        // Set employee growth data from API response
        if (dashboardData.employee_growth) {
          setEmployeeGrowthData(dashboardData.employee_growth);
        } else {
          // Fallback data if not available from API
          setEmployeeGrowthData([
            { month: 'Jan', employees: 142 },
            { month: 'Feb', employees: 145 },
            { month: 'Mar', employees: 148 },
            { month: 'Apr', employees: 152 },
            { month: 'May', employees: 155 },
            { month: 'Jun', employees: 158 },
            { month: 'Jul', employees: 162 },
            { month: 'Aug', employees: 165 },
            { month: 'Sep', employees: 168 },
            { month: 'Oct', employees: 172 },
            { month: 'Nov', employees: 175 },
            { month: 'Dec', employees: 178 }
          ]);
        }
        
        // Set department data from API response
        if (dashboardData.department_distribution) {
          setDepartmentData(dashboardData.department_distribution);
        } else {
          // Fallback data if not available from API
          setDepartmentData([
            { department: 'Engineering', count: 45, percentage: 30 },
            { department: 'Sales', count: 35, percentage: 23 },
            { department: 'Marketing', count: 25, percentage: 17 },
            { department: 'HR', count: 15, percentage: 10 },
            { department: 'Finance', count: 20, percentage: 13 },
            { department: 'Operations', count: 10, percentage: 7 }
          ]);
        }
        
      } catch (err) {
        console.error('Error fetching reports data:', err);
        setError('Failed to load reports data');
        // Set fallback data on error
        setAnalyticsData(defaultAnalyticsData);
        setEmployeeGrowthData([
          { month: 'Jan', employees: 142 },
          { month: 'Feb', employees: 145 },
          { month: 'Mar', employees: 148 },
          { month: 'Apr', employees: 152 },
          { month: 'May', employees: 155 },
          { month: 'Jun', employees: 158 },
          { month: 'Jul', employees: 162 },
          { month: 'Aug', employees: 165 },
          { month: 'Sep', employees: 168 },
          { month: 'Oct', employees: 172 },
          { month: 'Nov', employees: 175 },
          { month: 'Dec', employees: 178 }
        ]);
        setDepartmentData([
          { department: 'Engineering', count: 45, percentage: 30 },
          { department: 'Sales', count: 35, percentage: 23 },
          { department: 'Marketing', count: 25, percentage: 17 },
          { department: 'HR', count: 15, percentage: 10 },
          { department: 'Finance', count: 20, percentage: 13 },
          { department: 'Operations', count: 10, percentage: 7 }
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchReportsData();
  }, []);

  const handleGenerateCustomReport = () => {
    setShowCustomReportModal(true);
  };

  const handleGenerateReport = async (report: any) => {
    console.log('Generating report for:', report);
    console.log('Report details:', report);
    setSelectedReport(report);
    setShowGenerateReportModal(true);
  };

  const handleDownloadReport = (report: any) => {
    console.log('Downloading report:', report.name);
    // Simulate download
    const link = document.createElement('a');
    link.href = 'data:text/plain;charset=utf-8,' + encodeURIComponent(`Report: ${report.name}\nGenerated: ${new Date().toLocaleDateString()}\nContent: This is a sample report content.`);
    link.download = `${report.name.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.txt`;
    link.click();
  };

  const handleShareReport = (report: any) => {
    console.log('Sharing report:', report.name);
    alert(`Sharing report: ${report.name}\nThis would open a share dialog in a real application.`);
  };

  const handleScheduleReport = (reportData: any) => {
    console.log('Scheduling report:', reportData);
    alert(`Report scheduled successfully!\nType: ${reportData.type}\nFrequency: ${reportData.frequency}\nRecipients: ${reportData.recipients}`);
  };

  const handleDisableScheduledReport = (reportName: string) => {
    console.log('Disabling scheduled report:', reportName);
    alert(`Scheduled report "${reportName}" has been disabled.`);
  };

  const generateCustomReportDataByType = (reportType: string, format: string, apiData?: any) => {
    let content = '';
    const separator = format === 'csv' ? ',' : format === 'excel' ? '\t' : ' | ';
    
    console.log('Generating custom report data for type:', reportType, 'format:', format);
    
    switch (reportType.toLowerCase()) {
      case 'employee':
      case 'employees':
        if (format === 'pdf') {
          content += `EMPLOYEE DIRECTORY\n`;
          content += `=================\n`;
          content += `ID${separator}Name${separator}Department${separator}Position${separator}Salary${separator}Status\n`;
        } else {
          content += `Employee ID${separator}Name${separator}Department${separator}Position${separator}Salary${separator}Status\n`;
        }
        content += `1${separator}John Doe${separator}Engineering${separator}Software Engineer${separator}75000${separator}Active\n`;
        content += `2${separator}Jane Smith${separator}Sales${separator}Sales Manager${separator}65000${separator}Active\n`;
        content += `3${separator}Mike Johnson${separator}Marketing${separator}Marketing Specialist${separator}55000${separator}Active\n`;
        content += `4${separator}Sarah Wilson${separator}HR${separator}HR Manager${separator}70000${separator}Active\n`;
        content += `5${separator}David Brown${separator}Finance${separator}Financial Analyst${separator}60000${separator}Active\n`;
        break;
        
      case 'attendance':
        if (format === 'pdf') {
          content += `ATTENDANCE REPORT\n`;
          content += `=================\n`;
          content += `ID${separator}Name${separator}Date${separator}Check In${separator}Check Out${separator}Hours\n`;
        } else {
          content += `Employee ID${separator}Name${separator}Date${separator}Check In${separator}Check Out${separator}Hours Worked\n`;
        }
        content += `1${separator}John Doe${separator}2024-01-15${separator}09:00${separator}17:00${separator}8.0\n`;
        content += `2${separator}Jane Smith${separator}2024-01-15${separator}08:30${separator}17:30${separator}8.5\n`;
        content += `3${separator}Mike Johnson${separator}2024-01-15${separator}09:15${separator}17:15${separator}8.0\n`;
        content += `4${separator}Sarah Wilson${separator}2024-01-15${separator}09:00${separator}17:00${separator}8.0\n`;
        content += `5${separator}David Brown${separator}2024-01-15${separator}08:45${separator}17:15${separator}8.5\n`;
        break;
        
      case 'payroll':
        if (format === 'pdf') {
          content += `PAYROLL SUMMARY\n`;
          content += `===============\n`;
          content += `ID${separator}Name${separator}Department${separator}Base Salary${separator}Bonus${separator}Total\n`;
        } else {
          content += `Employee ID${separator}Name${separator}Department${separator}Base Salary${separator}Bonus${separator}Total\n`;
        }
        content += `1${separator}John Doe${separator}Engineering${separator}75000${separator}5000${separator}80000\n`;
        content += `2${separator}Jane Smith${separator}Sales${separator}65000${separator}8000${separator}73000\n`;
        content += `3${separator}Mike Johnson${separator}Marketing${separator}55000${separator}3000${separator}58000\n`;
        content += `4${separator}Sarah Wilson${separator}HR${separator}70000${separator}4000${separator}74000\n`;
        content += `5${separator}David Brown${separator}Finance${separator}60000${separator}2000${separator}62000\n`;
        break;
        
      case 'training':
        if (format === 'pdf') {
          content += `TRAINING COMPLETION REPORT\n`;
          content += `========================\n`;
          content += `ID${separator}Name${separator}Department${separator}Course${separator}Status${separator}Completion Date\n`;
        } else {
          content += `Employee ID${separator}Name${separator}Department${separator}Course${separator}Status${separator}Completion Date\n`;
        }
        content += `1${separator}John Doe${separator}Engineering${separator}Advanced JavaScript${separator}Completed${separator}2024-01-10\n`;
        content += `2${separator}Jane Smith${separator}Sales${separator}Sales Techniques${separator}In Progress${separator}2024-01-15\n`;
        content += `3${separator}Mike Johnson${separator}Marketing${separator}Digital Marketing${separator}Completed${separator}2024-01-08\n`;
        content += `4${separator}Sarah Wilson${separator}HR${separator}HR Compliance${separator}Completed${separator}2024-01-12\n`;
        content += `5${separator}David Brown${separator}Finance${separator}Financial Analysis${separator}Not Started${separator}-\n`;
        break;
        
      case 'recruitment':
      case 'hiring':
        if (format === 'pdf') {
          content += `RECRUITMENT PIPELINE\n`;
          content += `===================\n`;
          content += `Position${separator}Department${separator}Status${separator}Days Open${separator}Candidates${separator}Source\n`;
        } else {
          content += `Position${separator}Department${separator}Status${separator}Days Open${separator}Candidates${separator}Source\n`;
        }
        content += `Software Engineer${separator}Engineering${separator}Open${separator}15${separator}25${separator}LinkedIn\n`;
        content += `Sales Manager${separator}Sales${separator}Interviewing${separator}8${separator}12${separator}Indeed\n`;
        content += `Marketing Specialist${separator}Marketing${separator}Offer Sent${separator}12${separator}18${separator}Referral\n`;
        content += `HR Coordinator${separator}HR${separator}Closed${separator}5${separator}8${separator}Job Board\n`;
        content += `Financial Analyst${separator}Finance${separator}Open${separator}20${separator}15${separator}LinkedIn\n`;
        break;
        
      default:
        // Default to employee data if type is not recognized
        if (format === 'pdf') {
          content += `EMPLOYEE DIRECTORY\n`;
          content += `=================\n`;
          content += `ID${separator}Name${separator}Department${separator}Position${separator}Salary${separator}Status\n`;
        } else {
          content += `Employee ID${separator}Name${separator}Department${separator}Position${separator}Salary${separator}Status\n`;
        }
        content += `1${separator}John Doe${separator}Engineering${separator}Software Engineer${separator}75000${separator}Active\n`;
        content += `2${separator}Jane Smith${separator}Sales${separator}Sales Manager${separator}65000${separator}Active\n`;
        content += `3${separator}Mike Johnson${separator}Marketing${separator}Marketing Specialist${separator}55000${separator}Active\n`;
        content += `4${separator}Sarah Wilson${separator}HR${separator}HR Manager${separator}70000${separator}Active\n`;
        content += `5${separator}David Brown${separator}Finance${separator}Financial Analyst${separator}60000${separator}Active\n`;
    }
    
    return content;
  };

  const generateCustomReportContent = async (reportData: any) => {
    const currentDate = new Date().toLocaleDateString();
    const currentTime = new Date().toLocaleTimeString();
    
    console.log('Generating custom report with data:', reportData);
    console.log('Report type:', reportData.type);
    console.log('Report format:', reportData.format);
    
    try {
      // Fetch real data from API based on report type
      let apiData = null;
      
      switch (reportData.type.toLowerCase()) {
        case 'employee':
        case 'employees':
          const employeeResponse = await reportsAPI.getEmployeeReports();
          apiData = employeeResponse.data;
          break;
        case 'attendance':
          const attendanceResponse = await reportsAPI.getAttendanceReports();
          apiData = attendanceResponse.data;
          break;
        case 'payroll':
          const payrollResponse = await reportsAPI.getPayrollReports();
          apiData = payrollResponse.data;
          break;
        default:
          // Default to dashboard data
          const dashboardResponse = await reportsAPI.getDashboardData();
          apiData = dashboardResponse.data;
      }
      
      let content = '';
      
      switch (reportData.format) {
        case 'csv':
          content = `Report Title,${reportData.title}\n`;
          content += `Report Type,${reportData.type}\n`;
          content += `Date Range,${reportData.dateRange}\n`;
          content += `Generated Date,${currentDate}\n`;
          content += `Generated Time,${currentTime}\n\n`;
          content += generateCustomReportDataByType(reportData.type, 'csv', apiData);
          break;
          
        case 'excel':
          // For Excel, we'll create a CSV-like format that Excel can open
          content = `Report Title\t${reportData.title}\n`;
          content += `Report Type\t${reportData.type}\n`;
          content += `Date Range\t${reportData.dateRange}\n`;
          content += `Generated Date\t${currentDate}\n`;
          content += `Generated Time\t${currentTime}\n\n`;
          content += generateCustomReportDataByType(reportData.type, 'excel', apiData);
          break;
          
        default: // PDF format
          content = `HR PILOT SYSTEM - CUSTOM REPORT\n`;
          content += `================================\n\n`;
          content += `Report Title: ${reportData.title}\n`;
          content += `Report Type: ${reportData.type}\n`;
          content += `Date Range: ${reportData.dateRange}\n`;
          content += `Generated: ${currentDate} at ${currentTime}\n\n`;
          content += `SUMMARY\n`;
          content += `-------\n`;
          content += `Total Employees: ${apiData?.employee_count || 0}\n`;
          content += `Active Employees: ${apiData?.active_employees || 0}\n`;
          content += `New Hires This Month: ${apiData?.new_hires || 0}\n`;
          content += `Average Salary: $${apiData?.average_salary || 0}\n`;
          content += `Turnover Rate: ${apiData?.turnover_rate || 0}%\n\n`;
          content += generateCustomReportDataByType(reportData.type, 'pdf', apiData);
          content += `This report was generated automatically by the HR Pilot System.\n`;
          content += `For questions or support, please contact the HR department.\n`;
      }
      
      return content;
    } catch (error) {
      console.error('Error generating custom report:', error);
      // Fallback to static data if API fails
      return generateCustomReportContentFallback(reportData, currentDate, currentTime);
    }
  };
  
  const generateCustomReportContentFallback = (reportData: any, currentDate: string, currentTime: string) => {
    let content = '';
    
    switch (reportData.format) {
      case 'csv':
        content = `Report Title,${reportData.title}\n`;
        content += `Report Type,${reportData.type}\n`;
        content += `Date Range,${reportData.dateRange}\n`;
        content += `Generated Date,${currentDate}\n`;
        content += `Generated Time,${currentTime}\n\n`;
        content += generateCustomReportDataByType(reportData.type, 'csv');
        break;
        
      case 'excel':
        content = `Report Title\t${reportData.title}\n`;
        content += `Report Type\t${reportData.type}\n`;
        content += `Date Range\t${reportData.dateRange}\n`;
        content += `Generated Date\t${currentDate}\n`;
        content += `Generated Time\t${currentTime}\n\n`;
        content += generateCustomReportDataByType(reportData.type, 'excel');
        break;
        
      default: // PDF format
        content = `HR PILOT SYSTEM - CUSTOM REPORT\n`;
        content += `================================\n\n`;
        content += `Report Title: ${reportData.title}\n`;
        content += `Report Type: ${reportData.type}\n`;
        content += `Date Range: ${reportData.dateRange}\n`;
        content += `Generated: ${currentDate} at ${currentTime}\n\n`;
        content += `SUMMARY\n`;
        content += `-------\n`;
        content += `Total Employees: 150\n`;
        content += `Active Employees: 142\n`;
        content += `New Hires This Month: 8\n`;
        content += `Average Salary: $5,200\n`;
        content += `Turnover Rate: 5.3%\n\n`;
        content += generateCustomReportDataByType(reportData.type, 'pdf');
        content += `This report was generated automatically by the HR Pilot System.\n`;
        content += `For questions or support, please contact the HR department.\n`;
    }
    
    return content;
  };

  const generateReportDataByCategory = async (report: any, format: string) => {
    let content = '';
    const separator = format === 'csv' ? ',' : format === 'excel' ? '\t' : ' | ';
    
    // Find which category this report belongs to
    const category = reportCategories.find(cat => 
      cat.reports.some(r => r.name === report.name)
    );
    
    console.log('Generating report:', report.name);
    console.log('Found category:', category?.name);
    console.log('Format:', format);
    
    if (!category) {
      console.error('Report category not found for:', report.name);
      return 'Report category not found';
    }
    
    try {
      switch (category.name) {
        case 'Employee Reports':
          // Fetch real employee data from API
          const employeeResponse = await reportsAPI.getEmployeeReports();
          const employeeData = employeeResponse.data;
          
          if (format === 'pdf') {
            content += `EMPLOYEE DIRECTORY\n`;
            content += `=================\n`;
            content += `ID${separator}Name${separator}Department${separator}Position${separator}Status${separator}Hire Date\n`;
          } else {
            content += `Employee ID${separator}Name${separator}Department${separator}Position${separator}Status${separator}Hire Date\n`;
          }
          
          // Get actual employee data from backend using authenticated API
          try {
            const employeesResponse = await fetch('/api/v1/employees', {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
              }
            });
            
            if (!employeesResponse.ok) {
              throw new Error(`HTTP error! status: ${employeesResponse.status}`);
            }
            
            const employeesData = await employeesResponse.json();
            
            if (employeesData && Array.isArray(employeesData) && employeesData.length > 0) {
              employeesData.forEach((emp: any) => {
                const deptName = emp.department?.name || 'No Department';
                const position = emp.position || 'N/A';
                const hireDate = emp.hire_date ? new Date(emp.hire_date).toLocaleDateString() : 'N/A';
                content += `${emp.employee_id || emp.id}${separator}${emp.full_name || 'N/A'}${separator}${deptName}${separator}${position}${separator}${emp.status || 'N/A'}${separator}${hireDate}\n`;
              });
            } else {
              content += `No employees found in the system.\n`;
            }
          } catch (error: any) {
            console.error('Error fetching employee data:', error);
            content += `Error fetching employee data: ${error?.message || 'Unknown error'}\n`;
          }
          break;
        
        case 'Attendance Reports':
          // Fetch real attendance data from API
          const attendanceResponse = await reportsAPI.getAttendanceReports();
          const attendanceData = attendanceResponse.data;
          
          if (format === 'pdf') {
            content += `ATTENDANCE REPORT\n`;
            content += `=================\n`;
            content += `ID${separator}Name${separator}Date${separator}Check In${separator}Check Out${separator}Hours${separator}Status\n`;
          } else {
            content += `Employee ID${separator}Name${separator}Date${separator}Check In${separator}Check Out${separator}Hours Worked${separator}Status\n`;
          }
          
          // Get actual attendance data from backend using authenticated API
          try {
            const attendanceApiResponse = await fetch('/api/v1/attendance/history?start_date=2024-01-01&end_date=2024-12-31', {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
              }
            });
            
            if (!attendanceApiResponse.ok) {
              throw new Error(`HTTP error! status: ${attendanceApiResponse.status}`);
            }
            
            const attendanceApiData = await attendanceApiResponse.json();
            
            if (attendanceApiData && Array.isArray(attendanceApiData) && attendanceApiData.length > 0) {
              attendanceApiData.slice(0, 50).forEach((att: any) => { // Limit to 50 records for readability
                const checkIn = att.check_in_time ? new Date(att.check_in_time).toLocaleTimeString() : 'N/A';
                const checkOut = att.check_out_time ? new Date(att.check_out_time).toLocaleTimeString() : 'N/A';
                const date = att.date || 'N/A';
                const hours = att.total_hours || 'N/A';
                const employeeName = att.employee?.full_name || 'N/A';
                const employeeId = att.employee?.employee_id || att.employee_id || 'N/A';
                content += `${employeeId}${separator}${employeeName}${separator}${date}${separator}${checkIn}${separator}${checkOut}${separator}${hours}${separator}${att.status || 'N/A'}\n`;
              });
            } else {
              content += `No attendance records found in the system.\n`;
            }
          } catch (error: any) {
            console.error('Error fetching attendance data:', error);
            content += `Error fetching attendance data: ${error?.message || 'Unknown error'}\n`;
          }
          break;
        
        case 'Payroll Reports':
          // Fetch real payroll data from API
          const payrollResponse = await reportsAPI.getPayrollReports();
          const payrollData = payrollResponse.data;
          
          if (format === 'pdf') {
            content += `PAYROLL SUMMARY\n`;
            content += `===============\n`;
            content += `ID${separator}Name${separator}Department${separator}Basic Salary${separator}Allowances${separator}Deductions${separator}Net Pay${separator}Status\n`;
          } else {
            content += `Employee ID${separator}Name${separator}Department${separator}Basic Salary${separator}Allowances${separator}Deductions${separator}Net Pay${separator}Status\n`;
          }
          
          // Get actual payroll data from backend using authenticated API
          try {
            const payrollApiResponse = await fetch('/api/v1/payroll/records', {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
              }
            });
            
            if (!payrollApiResponse.ok) {
              throw new Error(`HTTP error! status: ${payrollApiResponse.status}`);
            }
            
            const payrollApiData = await payrollApiResponse.json();
            
            // Handle the API response structure (it returns {records: [...], total: N, ...})
            const payrollRecords = payrollApiData?.records || payrollApiData || [];
            
            if (payrollRecords && Array.isArray(payrollRecords) && payrollRecords.length > 0) {
              payrollRecords.forEach((payroll: any) => {
                const employeeName = payroll.employee || 'N/A'; // API returns employee name directly
                const employeeId = payroll.employee_id || 'N/A';
                const department = payroll.department || 'N/A';
                const basicSalary = payroll.basic_salary || 0;
                const allowances = payroll.allowances || 0;
                const deductions = payroll.deductions || 0;
                const netPay = payroll.net_salary || 0;
                const status = payroll.status || 'N/A';
                
                content += `${employeeId}${separator}${employeeName}${separator}${department}${separator}${basicSalary}${separator}${allowances}${separator}${deductions}${separator}${netPay}${separator}${status}\n`;
              });
            } else {
              content += `No payroll records found in the system.\n`;
            }
          } catch (error: any) {
            console.error('Error fetching payroll data:', error);
            content += `Error fetching payroll data: ${error?.message || 'Unknown error'}\n`;
          }
          break;
        
      case 'Recruitment Reports':
        if (format === 'pdf') {
          content += `RECRUITMENT PIPELINE\n`;
          content += `===================\n`;
          content += `Position${separator}Department${separator}Status${separator}Days Open${separator}Candidates${separator}Source\n`;
        } else {
          content += `Position${separator}Department${separator}Status${separator}Days Open${separator}Candidates${separator}Source\n`;
        }
        content += `Software Engineer${separator}Engineering${separator}Open${separator}15${separator}25${separator}LinkedIn\n`;
        content += `Sales Manager${separator}Sales${separator}Interviewing${separator}8${separator}12${separator}Indeed\n`;
        content += `Marketing Specialist${separator}Marketing${separator}Offer Sent${separator}12${separator}18${separator}Referral\n`;
        content += `HR Coordinator${separator}HR${separator}Closed${separator}5${separator}8${separator}Job Board\n`;
        content += `Financial Analyst${separator}Finance${separator}Open${separator}20${separator}15${separator}LinkedIn\n`;
        break;
        
      default:
        content += `Report data not available for this category.\n`;
    }
    } catch (error) {
      console.error('Error generating report data:', error);
      content += `Error generating report data. Please try again.\n`;
    }
    
    return content;
  };

  const generateSpecificReportContent = async (report: any, reportData: any) => {
    const currentDate = new Date().toLocaleDateString();
    const currentTime = new Date().toLocaleTimeString();
    
    let content = '';
    
    switch (reportData.format) {
      case 'csv':
        content = `Report Name,${report.name}\n`;
        content += `Description,${report.description}\n`;
        content += `Generated Date,${currentDate}\n`;
        content += `Generated Time,${currentTime}\n`;
        content += `Include Charts,${reportData.includeCharts ? 'Yes' : 'No'}\n\n`;
        
        // Generate content based on report category and type
        content += await generateReportDataByCategory(report, 'csv');
        break;
        
      case 'excel':
        content = `Report Name\t${report.name}\n`;
        content += `Description\t${report.description}\n`;
        content += `Generated Date\t${currentDate}\n`;
        content += `Generated Time\t${currentTime}\n`;
        content += `Include Charts\t${reportData.includeCharts ? 'Yes' : 'No'}\n\n`;
        
        content += await generateReportDataByCategory(report, 'excel');
        break;
        
      default: // PDF format
        content = `HR PILOT SYSTEM - ${report.name.toUpperCase()}\n`;
        content += `==========================================\n\n`;
        content += `Report Name: ${report.name}\n`;
        content += `Description: ${report.description}\n`;
        content += `Generated: ${currentDate} at ${currentTime}\n`;
        content += `Include Charts: ${reportData.includeCharts ? 'Yes' : 'No'}\n\n`;
        
        content += await generateReportDataByCategory(report, 'pdf');
        
        content += `\nThis report was generated automatically by the HR Pilot System.\n`;
        content += `For questions or support, please contact the HR department.\n`;
    }
    
    return content;
  };

  const downloadReport = (content: string, title: string, format: string) => {
    const fileName = `${title.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}`;
    let mimeType = 'text/plain';
    let fileExtension = 'txt';
    
    switch (format) {
      case 'csv':
        mimeType = 'text/csv';
        fileExtension = 'csv';
        break;
      case 'excel':
        mimeType = 'application/vnd.ms-excel';
        fileExtension = 'xls';
        break;
      case 'pdf':
        // For PDF, we'll create a properly formatted text file that can be opened
        // and then converted to PDF using the user's PDF viewer
        mimeType = 'text/plain';
        fileExtension = 'txt';
        // Add PDF header to make it more readable
        content = `=== HR PILOT SYSTEM REPORT ===\n\n${content}\n\nGenerated on: ${new Date().toLocaleString()}\n`;
        break;
    }
    
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${fileName}.${fileExtension}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    // Show success message with format-specific instructions
    if (format === 'pdf') {
      alert(`Report "${title}" has been downloaded as a text file.\n\nTo convert to PDF:\n1. Open the file in any text editor\n2. Use "Print" and select "Save as PDF"\n3. Or use online converters like smallpdf.com`);
    } else {
      alert(`Report "${title}" has been generated and downloaded successfully!`);
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
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Reports</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()}
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
            <h1 className="text-2xl font-bold text-gray-900">Reports & Analytics</h1>
            <p className="text-gray-600">Generate and view HR reports and analytics</p>
          </div>
          <button 
            onClick={handleGenerateCustomReport}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md"
          >
            Generate Custom Report
          </button>
        </div>

        {/* Analytics Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <span className="text-blue-600 text-xl">👥</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Employees</p>
                <p className="text-2xl font-semibold text-gray-900">{analyticsData?.totalEmployees || 0}</p>
                <p className="text-xs text-green-600">+8 this month</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <span className="text-green-600 text-xl">📊</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Turnover Rate</p>
                <p className="text-2xl font-semibold text-gray-900">{analyticsData?.turnoverRate || 0}%</p>
                <p className="text-xs text-green-600">-0.5% from last month</p>
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
                <p className="text-2xl font-semibold text-gray-900">${analyticsData?.totalPayroll ? (analyticsData.totalPayroll / 1000).toFixed(0) : 0}K</p>
                <p className="text-xs text-green-600">+5.2% from last month</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <span className="text-yellow-600 text-xl">⏰</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Attendance Rate</p>
                <p className="text-2xl font-semibold text-gray-900">{analyticsData?.averageAttendance || 0}%</p>
                <p className="text-xs text-green-600">+1.2% from last month</p>
              </div>
            </div>
          </div>
        </div>

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
                Overview
              </button>
              {false && (
                <button
                  onClick={() => setActiveTab('reports')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'reports'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Available Reports
                </button>
              )}
              <button
                onClick={() => setActiveTab('recent')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'recent'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Recent Reports
              </button>
              <button
                onClick={() => setActiveTab('scheduled')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'scheduled'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Scheduled Reports
              </button>
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Employee Growth</h3>
                    <div className="space-y-3">
                      {employeeGrowthData.map((data, index) => (
                        <div key={index} className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">{data.month}</span>
                          <div className="flex items-center space-x-2">
                            <div className="w-32 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full" 
                                style={{ width: `${(data.employees / 200) * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-sm font-medium text-gray-900">{data.employees}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Department Distribution</h3>
                    <div className="space-y-3">
                      {departmentData.map((dept, index) => (
                        <div key={index} className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">{dept.department}</span>
                          <div className="flex items-center space-x-2">
                            <div className="w-32 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-green-600 h-2 rounded-full" 
                                style={{ width: `${dept.percentage}%` }}
                              ></div>
                            </div>
                            <span className="text-sm font-medium text-gray-900">{dept.count}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Key Metrics */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Key Metrics</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="text-blue-600 font-semibold">Average Salary</div>
                      <div className="text-2xl font-bold text-blue-900">${analyticsData?.averageSalary || 0}</div>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="text-green-600 font-semibold">New Hires This Month</div>
                      <div className="text-2xl font-bold text-green-900">{analyticsData?.newHires || 0}</div>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <div className="text-purple-600 font-semibold">Pending Leave Requests</div>
                      <div className="text-2xl font-bold text-purple-900">{analyticsData?.pendingLeaveRequests || 0}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {false &&
              activeTab === 'reports' && (
                <div className="space-y-6">
                  {reportCategories.map((category) => (
                    <div key={category.name} className="border border-gray-200 rounded-lg">
                      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                        <div className="flex items-center">
                          <span className="text-2xl mr-3">{category.icon}</span>
                          <h3 className="text-lg font-medium text-gray-900">{category.name}</h3>
                        </div>
                      </div>
                      <div className="p-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {category.reports.map((report) => (
                            <div key={report.name} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                              <div className="flex justify-between items-start">
                                <div>
                                  <h4 className="font-medium text-gray-900">{report.name}</h4>
                                  <p className="text-sm text-gray-600 mt-1">{report.description}</p>
                                </div>
                                <button 
                                  onClick={() => handleGenerateReport(report)}
                                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1 rounded text-sm"
                                >
                                  Generate
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

            {activeTab === 'recent' && (
              <div>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Recent Reports</h3>
                  <button className="text-indigo-600 hover:text-indigo-900 text-sm">View All</button>
                </div>
                <div className="space-y-3">
                  {recentReports.map((report, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center">
                        <div className="p-2 bg-white rounded-lg mr-4">
                          <span className="text-gray-600">
                            {report.type === 'PDF' ? '📄' : '📊'}
                          </span>
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{report.name}</div>
                          <div className="text-sm text-gray-500">{report.date} • {report.size}</div>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <button 
                          onClick={() => handleDownloadReport(report)}
                          className="text-indigo-600 hover:text-indigo-900 text-sm"
                        >
                          Download
                        </button>
                        <button 
                          onClick={() => handleShareReport(report)}
                          className="text-gray-600 hover:text-gray-900 text-sm"
                        >
                          Share
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'scheduled' && (
              <div className="space-y-6">
                <div className="bg-gray-50 p-6 rounded-lg">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Scheduled Reports</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-white rounded-lg">
                      <div>
                        <div className="font-medium text-gray-900">Monthly Payroll Report</div>
                        <div className="text-sm text-gray-500">Generated on the 1st of every month</div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                          Active
                        </span>
                        <button 
                          onClick={() => handleDisableScheduledReport('Monthly Payroll Report')}
                          className="text-red-600 hover:text-red-900 text-sm"
                        >
                          Disable
                        </button>
                      </div>
                    </div>
                    <div className="flex items-center justify-between p-4 bg-white rounded-lg">
                      <div>
                        <div className="font-medium text-gray-900">Weekly Attendance Report</div>
                        <div className="text-sm text-gray-500">Generated every Monday</div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                          Active
                        </span>
                        <button 
                          onClick={() => handleDisableScheduledReport('Weekly Attendance Report')}
                          className="text-red-600 hover:text-red-900 text-sm"
                        >
                          Disable
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 p-6 rounded-lg">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Schedule New Report</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Report Type</label>
                      <select className="w-full px-3 py-2 border border-gray-300 rounded-md">
                        <option>Select a report type</option>
                        <option>Employee Directory</option>
                        <option>Payroll Summary</option>
                        <option>Attendance Report</option>
                        <option>Training Completion</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Frequency</label>
                      <select className="w-full px-3 py-2 border border-gray-300 rounded-md">
                        <option>Daily</option>
                        <option>Weekly</option>
                        <option>Monthly</option>
                        <option>Quarterly</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Recipients</label>
                      <input
                        type="email"
                        placeholder="Enter email addresses"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      />
                    </div>
                    <button 
                      onClick={() => {
                        const formData = new FormData(document.querySelector('form') as HTMLFormElement);
                        handleScheduleReport({
                          type: formData.get('reportType'),
                          frequency: formData.get('frequency'),
                          recipients: formData.get('recipients')
                        });
                      }}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md"
                    >
                      Schedule Report
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Custom Report Modal */}
        {showCustomReportModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Generate Custom Report</h3>
                  <button
                    onClick={() => setShowCustomReportModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>
                
                <form onSubmit={async (e) => {
                  e.preventDefault();
                  const formData = new FormData(e.currentTarget);
                  const reportData = {
                    title: formData.get('title'),
                    type: formData.get('type'),
                    dateRange: formData.get('dateRange'),
                    format: formData.get('format')
                  };
                  console.log('Generating custom report:', reportData);
                  
                  try {
                    // Generate and download the report
                    const reportContent = await generateCustomReportContent(reportData);
                    downloadReport(reportContent, reportData.title as string, reportData.format as string);
                    
                    setShowCustomReportModal(false);
                  } catch (error) {
                    console.error('Error generating report:', error);
                    alert('Error generating report. Please try again.');
                  }
                }}>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Report Title</label>
                      <input
                        type="text"
                        name="title"
                        required
                        placeholder="Enter report title"
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Report Type</label>
                      <select
                        name="type"
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="">Select Report Type</option>
                        <option value="employee">Employee Report</option>
                        <option value="attendance">Attendance Report</option>
                        <option value="payroll">Payroll Report</option>
                        <option value="training">Training Report</option>
                        <option value="expenses">Expense Report</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Date Range</label>
                      <select
                        name="dateRange"
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="last7days">Last 7 Days</option>
                        <option value="last30days">Last 30 Days</option>
                        <option value="last3months">Last 3 Months</option>
                        <option value="last6months">Last 6 Months</option>
                        <option value="lastYear">Last Year</option>
                        <option value="custom">Custom Range</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Format</label>
                      <select
                        name="format"
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="csv">CSV (Excel compatible)</option>
                        <option value="excel">Excel (.xls)</option>
                        <option value="pdf">Text (convertible to PDF)</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex justify-end space-x-3 mt-6">
                    <button
                      type="button"
                      onClick={() => setShowCustomReportModal(false)}
                      className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                    >
                      Generate Report
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Generate Report Modal */}
        {showGenerateReportModal && selectedReport && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Generate Report</h3>
                  <button
                    onClick={() => setShowGenerateReportModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>
                
                <div className="mb-4">
                  <h4 className="font-medium text-gray-900">{selectedReport.name}</h4>
                  <p className="text-sm text-gray-600 mt-1">{selectedReport.description}</p>
                </div>
                
                <form onSubmit={async (e) => {
                  e.preventDefault();
                  const formData = new FormData(e.currentTarget);
                  const reportData = {
                    report: selectedReport.name,
                    format: formData.get('format'),
                    includeCharts: formData.get('includeCharts')
                  };
                  console.log('Generating report:', reportData);
                  
                  try {
                    // Generate and download the specific report
                    const reportContent = await generateSpecificReportContent(selectedReport, reportData);
                    downloadReport(reportContent, selectedReport.name, reportData.format as string);
                    
                    setShowGenerateReportModal(false);
                  } catch (error) {
                    console.error('Error generating report:', error);
                    alert('Error generating report. Please try again.');
                  }
                }}>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Format</label>
                      <select
                        name="format"
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="csv">CSV (Excel compatible)</option>
                        <option value="excel">Excel (.xls)</option>
                        <option value="pdf">Text (convertible to PDF)</option>
                      </select>
                    </div>
                    <div>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          name="includeCharts"
                          className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">Include charts and graphs</span>
                      </label>
                    </div>
                  </div>
                  <div className="flex justify-end space-x-3 mt-6">
                    <button
                      type="button"
                      onClick={() => setShowGenerateReportModal(false)}
                      className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                    >
                      Generate
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

export default Reports; 