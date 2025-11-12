import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { CircularProgress, Box, Typography, Alert } from '@mui/material';

const ProtectedRoute = ({ children, requiredRoles = [], requireAuth = true }) => {
  const { user, isAuthenticated, loading } = useSelector((state) => state.auth);
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '50vh',
        gap: 2
      }}>
        <CircularProgress size={60} />
        <Typography variant="body2" color="text.secondary">
          Verifying access...
        </Typography>
      </Box>
    );
  }

  // Redirect to login if not authenticated
  if (requireAuth && !isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role-based access
  if (requiredRoles.length > 0 && user && !requiredRoles.includes(user.role)) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Access Denied
        </Alert>
        <Typography variant="h6" gutterBottom>
          You don't have permission to access this page.
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Required roles: {requiredRoles.join(', ')}
          <br />
          Your role: {user.role}
        </Typography>
      </Box>
    );
  }

  return children;
};

export default ProtectedRoute;
