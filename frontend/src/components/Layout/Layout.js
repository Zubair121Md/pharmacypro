import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { unmatchedAPI } from '../../services/api';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  Menu,
  MenuItem,
  useTheme,
  useMediaQuery,
  Badge,
  Collapse,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Upload as UploadIcon,
  Analytics as AnalyticsIcon,
  AdminPanelSettings as AdminIcon,
  Settings as SettingsIcon,
  Assignment as UnmatchedIcon,
  Assignment as AssignmentIcon,
  History as HistoryIcon,
  AccountCircle,
  Logout,
  Build as GeneratorIcon,
  LocalPharmacy as PharmacyIcon,
  Inventory as ProductIcon,
  Person as DoctorIcon,
  ExpandLess,
  ExpandMore,
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { logout } from '../../store/slices/authSlice';

const drawerWidth = 240;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { text: 'File Upload', icon: <UploadIcon />, path: '/upload' },
  { text: 'Analytics', icon: <AnalyticsIcon />, path: '/analytics' },
  { text: 'Unmatched Records', icon: <UnmatchedIcon />, path: '/unmatched', badge: true },
  { text: 'Recent Uploads', icon: <HistoryIcon />, path: '/recent-uploads' },
  { text: 'Incomplete Records', icon: <AssignmentIcon />, path: '/incomplete' }, // Data quality tab
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
];

const adminMenuItems = [
  { text: 'Admin Panel', icon: <AdminIcon />, path: '/admin' },
];

function Layout() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [unmatchedCount, setUnmatchedCount] = useState(0);
  const [generatorOpen, setGeneratorOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);

  useEffect(() => {
    const fetchUnmatchedCount = async () => {
      try {
        const response = await unmatchedAPI.getUnmatchedRecords();
        setUnmatchedCount(response.data?.length || 0);
      } catch (error) {
        console.error('Failed to fetch unmatched count:', error);
      }
    };
    
    fetchUnmatchedCount();
  }, []);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleProfileMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    dispatch(logout());
    handleProfileMenuClose();
  };

  const handleNavigation = (path) => {
    navigate(path);
    if (isMobile) {
      setMobileOpen(false);
    }
  };

  const handleGeneratorToggle = () => {
    setGeneratorOpen(!generatorOpen);
  };

  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Pharmacy Revenue
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path)}
            >
              <ListItemIcon>
                {item.badge ? (
                  <Badge badgeContent={unmatchedCount} color="error">
                    {item.icon}
                  </Badge>
                ) : (
                  item.icon
                )}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
        
        {/* Master ID Generator Section */}
        <ListItem disablePadding>
          <ListItemButton onClick={handleGeneratorToggle}>
            <ListItemIcon>
              <GeneratorIcon />
            </ListItemIcon>
            <ListItemText primary="Master ID Generator" />
            {generatorOpen ? <ExpandLess /> : <ExpandMore />}
          </ListItemButton>
        </ListItem>
        <Collapse in={generatorOpen} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            <ListItemButton 
              sx={{ pl: 4 }}
              selected={location.pathname === '/generator/pharmacy'}
              onClick={() => handleNavigation('/generator/pharmacy')}
            >
              <ListItemIcon>
                <PharmacyIcon />
              </ListItemIcon>
              <ListItemText primary="Pharmacy" />
            </ListItemButton>
            <ListItemButton 
              sx={{ pl: 4 }}
              selected={location.pathname === '/generator/products'}
              onClick={() => handleNavigation('/generator/products')}
            >
              <ListItemIcon>
                <ProductIcon />
              </ListItemIcon>
              <ListItemText primary="Products" />
            </ListItemButton>
            <ListItemButton 
              sx={{ pl: 4 }}
              selected={location.pathname === '/generator/doctor'}
              onClick={() => handleNavigation('/generator/doctor')}
            >
              <ListItemIcon>
                <DoctorIcon />
              </ListItemIcon>
              <ListItemText primary="Doctor" />
            </ListItemButton>
          </List>
        </Collapse>
        {isAdmin && (
          <>
            <Divider />
            {adminMenuItems.map((item) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton
                  selected={location.pathname === item.path}
                  onClick={() => handleNavigation(item.path)}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </>
        )}
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Pharmacy Revenue Management System
          </Typography>
          <IconButton
            size="large"
            edge="end"
            aria-label="account of current user"
            aria-controls="primary-search-account-menu"
            aria-haspopup="true"
            onClick={handleProfileMenuOpen}
            color="inherit"
          >
            <AccountCircle />
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            anchorOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            keepMounted
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            open={Boolean(anchorEl)}
            onClose={handleProfileMenuClose}
          >
            <MenuItem onClick={handleLogout}>
              <ListItemIcon>
                <Logout fontSize="small" />
              </ListItemIcon>
              Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
        aria-label="mailbox folders"
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${drawerWidth}px)` },
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}

export default Layout;
