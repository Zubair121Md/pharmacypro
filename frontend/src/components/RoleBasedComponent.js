import React from 'react';
import { useSelector } from 'react-redux';
import { Alert, Box, Typography } from '@mui/material';

const RoleBasedComponent = ({ 
  children, 
  allowedRoles = [], 
  fallback = null,
  showAccessDenied = true 
}) => {
  const { user, isAuthenticated } = useSelector((state) => state.auth);

  // If no roles specified, show to all authenticated users
  if (allowedRoles.length === 0) {
    return isAuthenticated ? children : null;
  }

  // Check if user has required role
  const hasAccess = isAuthenticated && user && allowedRoles.includes(user.role);

  if (hasAccess) {
    return children;
  }

  // Show fallback or access denied message
  if (fallback) {
    return fallback;
  }

  if (showAccessDenied) {
    return (
      <Alert severity="warning" sx={{ mb: 2 }}>
        <Typography variant="body2">
          This feature is only available to: {allowedRoles.join(', ')}
        </Typography>
      </Alert>
    );
  }

  return null;
};

export default RoleBasedComponent;
