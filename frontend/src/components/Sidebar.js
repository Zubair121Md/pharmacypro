import React from 'react';
import { useSelector } from 'react-redux';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Box,
  Typography,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Upload as UploadIcon,
  Analytics as AnalyticsIcon,
  AdminPanelSettings as AdminIcon,
  Settings as SettingsIcon,
  Warning as UnmatchedIcon,
  DataObject as DataManagementIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const drawerWidth = 240;

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useSelector((state) => state.auth);

  const menuItems = [
    {
      text: 'Dashboard',
      icon: <DashboardIcon />,
      path: '/dashboard',
    },
    {
      text: 'File Upload',
      icon: <UploadIcon />,
      path: '/upload',
    },
    {
      text: 'Analytics',
      icon: <AnalyticsIcon />,
      path: '/analytics',
    },
    {
      text: 'Data Management',
      icon: <DataManagementIcon />,
      path: '/data-management',
    },
    {
      text: 'Unmatched Records',
      icon: <UnmatchedIcon />,
      path: '/unmatched',
    },
    ...(user?.role === 'admin' || user?.role === 'super_admin'
      ? [
          {
            text: 'Admin Panel',
            icon: <AdminIcon />,
            path: '/admin',
          },
        ]
      : []),
    {
      text: 'Settings',
      icon: <SettingsIcon />,
      path: '/settings',
    },
  ];

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" color="primary">
          Navigation
        </Typography>
      </Box>
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
};

export default Sidebar;
