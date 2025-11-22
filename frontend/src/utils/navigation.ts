import { UserRole } from '../types';

export interface NavigationItem {
  name: string;
  href: string;
  icon: string;
  roles: UserRole[];
  description?: string;
}

export const navigationItems: NavigationItem[] = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: '📊',
    roles: [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.PAYROLL, UserRole.EMPLOYEE],
    description: 'Main dashboard'
  },
  {
    name: 'Users',
    href: '/users',
    icon: '👥',
    roles: [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR],
    description: 'Manage system users'
  },
  {
    name: 'Organizations',
    href: '/organizations',
    icon: '🏢',
    roles: [UserRole.SUPER_ADMIN],
    description: 'Manage organizations'
  },
  {
    name: 'Employees',
    href: '/employees',
    icon: '👤',
    roles: [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR],
    description: 'Manage employee records'
  },
  {
    name: 'Departments',
    href: '/departments',
    icon: '🏗️',
    roles: [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR],
    description: 'Manage departments'
  },
  {
    name: 'Attendance',
    href: '/attendance',
    icon: '⏰',
    roles: [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EMPLOYEE],
    description: 'Track attendance'
  },
  {
    name: 'Leave Management',
    href: '/leave',
    icon: '📅',
    roles: [UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EMPLOYEE],
    description: 'Manage leave requests'
  },
  {
    name: 'Payroll',
    href: '/payroll',
    icon: '💰',
    roles: [UserRole.PAYROLL, UserRole.HR, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN],
    description: 'Manage payroll'
  },
  {
    name: 'Documents',
    href: '/documents',
    icon: '📄',
    roles: [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EMPLOYEE],
    description: 'Manage documents'
  },
  {
    name: 'Training',
    href: '/training',
    icon: '🎓',
    roles: [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EMPLOYEE],
    description: 'Manage training programs'
  },
  {
    name: 'Expenses',
    href: '/expenses',
    icon: '💳',
    roles: [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR],
    description: 'Manage expenses'
  },
  {
    name: 'Reports',
    href: '/reports',
    icon: '📈',
    roles: [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.DIRECTOR, UserRole.PAYROLL],
    description: 'View reports and analytics'
  },
  {
    name: 'Profile',
    href: '/profile',
    icon: '👤',
    roles: [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.PAYROLL, UserRole.EMPLOYEE],
    description: 'Manage your profile and settings'
  },
  {
    name: 'AI Tools',
    href: '/ai-tools',
    icon: '🤖',
    roles: [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.PAYROLL, UserRole.EMPLOYEE],
    description: 'Curated list of popular enterprise AI tools'
  },
];

export const getNavigationForRole = (role: UserRole): NavigationItem[] => {
  return navigationItems.filter(item => item.roles.includes(role));
};

export const canAccessRoute = (route: string, role: UserRole): boolean => {
  const item = navigationItems.find(nav => nav.href === route);
  return item ? item.roles.includes(role) : false;
}; 