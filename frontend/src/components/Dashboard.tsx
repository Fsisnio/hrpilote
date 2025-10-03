import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { UserRole } from '../types';
import SuperAdminDashboard from './dashboards/SuperAdminDashboard';
import HRDashboard from './dashboards/HRDashboard';
import EmployeeDashboard from './dashboards/EmployeeDashboard';
import PayrollDashboard from './dashboards/PayrollDashboard';
import ManagerDashboard from './dashboards/ManagerDashboard';
import OrgAdminDashboard from './dashboards/OrgAdminDashboard';

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  if (!user) {
    return <div>Loading...</div>;
  }

  // Debug: Log user role for troubleshooting
  console.log('Dashboard - User role:', user.role, 'Type:', typeof user.role);
  console.log('Dashboard - UserRole.EMPLOYEE:', UserRole.EMPLOYEE);
  console.log('Dashboard - Role comparison:', user.role === UserRole.EMPLOYEE);
  console.log('Dashboard - Full user object:', user);

  // Route to appropriate dashboard based on user role
  switch (user.role) {
    case UserRole.SUPER_ADMIN:
      console.log('Routing to SuperAdminDashboard');
      return <SuperAdminDashboard />;
    
    case UserRole.ORG_ADMIN:
      console.log('Routing to OrgAdminDashboard');
      return <OrgAdminDashboard />;
    
    case UserRole.HR:
      console.log('Routing to HRDashboard');
      return <HRDashboard />;
    
    case UserRole.PAYROLL:
      console.log('Routing to PayrollDashboard');
      return <PayrollDashboard />;
    
    case UserRole.MANAGER:
    case UserRole.DIRECTOR:
      console.log('Routing to ManagerDashboard');
      return <ManagerDashboard />;
    
    case UserRole.EMPLOYEE:
      console.log('Routing to EmployeeDashboard');
      return <EmployeeDashboard />;
    
    default:
      console.log('Routing to EmployeeDashboard (default)');
      return <EmployeeDashboard />;
  }
};

export default Dashboard; 