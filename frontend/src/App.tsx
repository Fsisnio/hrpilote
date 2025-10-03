import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import ProtectedRoute from './components/ProtectedRoute';
import RoleBasedRoute from './components/RoleBasedRoute';

// Import all pages
import Users from './pages/Users';
import Organizations from './pages/Organizations';
import Employees from './pages/Employees';
import Departments from './pages/Departments';
import Attendance from './pages/Attendance';
import Leave from './pages/Leave';
import Payroll from './pages/Payroll';
import Documents from './pages/Documents';
import Training from './pages/Training';
import Expenses from './pages/Expenses';
import Reports from './pages/Reports';
import Profile from './pages/Profile';
import AITools from './pages/AITools';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/users"
              element={
                <ProtectedRoute>
                  <RoleBasedRoute requiredRoles={['SUPER_ADMIN', 'ORG_ADMIN', 'HR']}>
                    <Users />
                  </RoleBasedRoute>
                </ProtectedRoute>
              }
            />
            <Route
              path="/organizations"
              element={
                <ProtectedRoute>
                  <RoleBasedRoute requiredRoles={['SUPER_ADMIN']}>
                    <Organizations />
                  </RoleBasedRoute>
                </ProtectedRoute>
              }
            />
            <Route
              path="/employees"
              element={
                <ProtectedRoute>
                  <RoleBasedRoute requiredRoles={['SUPER_ADMIN', 'ORG_ADMIN', 'HR', 'MANAGER', 'DIRECTOR']}>
                    <Employees />
                  </RoleBasedRoute>
                </ProtectedRoute>
              }
            />
            <Route
              path="/departments"
              element={
                <ProtectedRoute>
                  <RoleBasedRoute requiredRoles={['SUPER_ADMIN', 'ORG_ADMIN', 'HR']}>
                    <Departments />
                  </RoleBasedRoute>
                </ProtectedRoute>
              }
            />
            <Route
              path="/attendance"
              element={
                <ProtectedRoute>
                  <RoleBasedRoute>
                    <Attendance />
                  </RoleBasedRoute>
                </ProtectedRoute>
              }
            />
            <Route
              path="/leave"
              element={
                <ProtectedRoute>
                  <RoleBasedRoute>
                    <Leave />
                  </RoleBasedRoute>
                </ProtectedRoute>
              }
            />
            <Route
              path="/payroll"
              element={
                <ProtectedRoute>
                  <RoleBasedRoute requiredRoles={['SUPER_ADMIN', 'ORG_ADMIN', 'PAYROLL']}>
                    <Payroll />
                  </RoleBasedRoute>
                </ProtectedRoute>
              }
            />
            <Route
              path="/documents"
              element={
                <ProtectedRoute>
                  <RoleBasedRoute>
                    <Documents />
                  </RoleBasedRoute>
                </ProtectedRoute>
              }
            />
            <Route
              path="/training"
              element={
                <ProtectedRoute>
                  <RoleBasedRoute>
                    <Training />
                  </RoleBasedRoute>
                </ProtectedRoute>
              }
            />
            <Route
              path="/expenses"
              element={
                <ProtectedRoute>
                  <RoleBasedRoute requiredRoles={['SUPER_ADMIN', 'ORG_ADMIN', 'HR', 'MANAGER', 'DIRECTOR']}>
                    <Expenses />
                  </RoleBasedRoute>
                </ProtectedRoute>
              }
            />
            <Route
              path="/reports"
              element={
                <ProtectedRoute>
                  <RoleBasedRoute requiredRoles={['SUPER_ADMIN', 'ORG_ADMIN', 'HR', 'DIRECTOR', 'PAYROLL']}>
                    <Reports />
                  </RoleBasedRoute>
                </ProtectedRoute>
              }
            />
            <Route
              path="/ai-tools"
              element={
                <ProtectedRoute>
                  <RoleBasedRoute>
                    <AITools />
                  </RoleBasedRoute>
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              }
            />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
