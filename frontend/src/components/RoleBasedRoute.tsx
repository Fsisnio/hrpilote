import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { canAccessRoute } from '../utils/navigation';
import UnauthorizedAccess from './UnauthorizedAccess';

interface RoleBasedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
  fallbackPath?: string;
}

const RoleBasedRoute: React.FC<RoleBasedRouteProps> = ({ 
  children, 
  requiredRoles = [], 
  fallbackPath = '/dashboard' 
}) => {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // If no specific roles are required, check if user can access the current route
  if (requiredRoles.length === 0) {
    const currentPath = window.location.pathname;
    if (!canAccessRoute(currentPath, user.role)) {
      return <UnauthorizedAccess />;
    }
  } else {
    // Check if user has any of the required roles
    const hasRequiredRole = requiredRoles.includes(user.role);
    if (!hasRequiredRole) {
      return <UnauthorizedAccess />;
    }
  }

  return <>{children}</>;
};

export default RoleBasedRoute; 