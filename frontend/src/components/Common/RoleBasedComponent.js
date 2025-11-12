import React from 'react';
import { useSelector } from 'react-redux';
import { Alert, Box } from '@mui/material';

function RoleBasedComponent({ children, allowedRoles = [] }) {
  const { user } = useSelector((state) => state.auth);

  if (!user) {
    return (
      <Alert severity="error">
        User not authenticated
      </Alert>
    );
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="warning">
          You don't have permission to access this page. Required roles: {allowedRoles.join(', ')}. Your role: {user.role}
        </Alert>
      </Box>
    );
  }

  return children;
}

export default RoleBasedComponent;
