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
  Button,
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
  Storage as MasterDataIcon,
  CheckCircle as NewlyMappedIcon,
  Refresh as RefreshIcon,
  DeleteSweep as DeleteSweepIcon,
  CallSplit as SplitRatioIcon,
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { logout } from '../../store/slices/authSlice';
import { adminAPI } from '../../services/api';

const drawerWidth = 240;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { text: 'File Upload', icon: <UploadIcon />, path: '/upload' },
  { text: 'Master Data Management', icon: <MasterDataIcon />, path: '/master-data' },
  { text: 'Split Ratio Management', icon: <SplitRatioIcon />, path: '/split-ratios' },
  { text: 'Analytics', icon: <AnalyticsIcon />, path: '/analytics' },
  { text: 'Unmatched Records', icon: <UnmatchedIcon />, path: '/unmatched', badge: true },
  { text: 'Newly Mapped', icon: <NewlyMappedIcon />, path: '/newly-mapped' },
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
  const [resettingSystem, setResettingSystem] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  const { user, token: reduxToken } = useSelector((state) => state.auth);

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

  const handleResetSystem = async () => {
    if (!window.confirm('Are you sure you want to reset the entire system? This will delete all invoices, unmatched records, and recent uploads. Master data, product reference, and split ratios will be preserved. This action cannot be undone.')) {
      return;
    }
    
    setResettingSystem(true);
    try {
      console.log('Attempting to reset system...');
      console.log('Current user:', user);
      console.log('User role:', user?.role);
      const localStorageToken = localStorage.getItem('token');
      const token = localStorageToken || reduxToken;
      console.log('Token from localStorage:', localStorageToken ? `${localStorageToken.substring(0, 20)}...` : 'NO TOKEN');
      console.log('Token from Redux:', reduxToken ? `${reduxToken.substring(0, 20)}...` : 'NO TOKEN');
      console.log('Using token:', token ? `${token.substring(0, 20)}...` : 'NO TOKEN');
      console.log('API Base URL:', process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000');
      
      if (!token) {
        alert('No authentication token found. Please log in again.');
        setResettingSystem(false);
        return;
      }
      
      // Test API connection first
      try {
        const testResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000'}/health`, {
          method: 'GET',
        });
        console.log('Health check response:', testResponse.status);
      } catch (testError) {
        console.error('Health check failed:', testError);
        alert('Cannot connect to backend server. Please ensure the backend is running on port 8000.');
        setResettingSystem(false);
        return;
      }
      
      const response = await adminAPI.resetSystem();
      console.log('Reset system response:', response);
      console.log('Response status:', response?.status);
      console.log('Response data:', response?.data);
      
      const productCount = response?.data?.product_data_count;
      const productPreserved = response?.data?.product_data_preserved;
      const splitRulesCount = response?.data?.split_rules_count;
      const splitRulesPreserved = response?.data?.split_rules_preserved;
      
      const extraMessage = productCount !== undefined
        ? `Product data ${productPreserved ? 'preserved' : 'status unknown'} (${productCount} records). Split rules ${splitRulesPreserved ? 'preserved' : 'status unknown'} (${splitRulesCount || 0} rules).`
        : 'Product data and split rules preserved.';
      
      // Use both alert and console for Tauri compatibility
      const successMsg = `System reset successfully! Master data has been preserved. ${extraMessage}`;
      alert(successMsg);
      console.log('SUCCESS:', successMsg);
      
      // Small delay before reload to ensure message is seen
      setTimeout(() => {
        window.location.reload();
      }, 500);
    } catch (error) {
      console.error('Failed to reset system:', error);
      console.error('Error type:', error.constructor.name);
      console.error('Error message:', error.message);
      console.error('Error response:', error.response);
      console.error('Error status:', error.response?.status);
      console.error('Error data:', error.response?.data);
      console.error('Error config:', error.config);
      
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error occurred';
      const statusCode = error.response?.status;
      
      let userMessage = `Failed to reset system`;
      if (statusCode === 401) {
        userMessage = 'Authentication failed. Please log in again. Your session may have expired.';
      } else if (statusCode === 403) {
        userMessage = `You do not have permission to reset the system. Admin access required. Current role: ${user?.role || 'unknown'}`;
      } else if (statusCode === 404) {
        userMessage = 'Reset endpoint not found. Please check if the backend is running correctly.';
      } else if (statusCode === 500) {
        userMessage = `Server error: ${errorMessage}`;
      } else if (statusCode) {
        userMessage = `Failed to reset system (Error ${statusCode}): ${errorMessage}`;
      } else if (error.message?.includes('Network Error') || error.message?.includes('Failed to fetch')) {
        userMessage = 'Network error: Cannot connect to backend server. Please ensure the backend is running on port 8000.';
      } else {
        userMessage = `Failed to reset system: ${errorMessage}`;
      }
      
      // Use both alert and console for Tauri compatibility
      alert(userMessage);
      console.error('ERROR:', userMessage);
    } finally {
      setResettingSystem(false);
    }
  };

  const handleResetMasterData = async () => {
    if (!window.confirm('Are you sure you want to reset master data management? This will delete all master data records. This action cannot be undone.')) {
      return;
    }
    try {
      await adminAPI.resetMasterData();
      alert('Master data reset successfully!');
      window.location.reload();
    } catch (error) {
      console.error('Failed to reset master data:', error);
      alert('Failed to reset master data. Please try again.');
    }
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
          {(user?.role === 'admin' || user?.role === 'super_admin') && (
            <>
              <Button
                variant="outlined"
                color="warning"
                size="small"
                startIcon={<RefreshIcon />}
                onClick={handleResetSystem}
                disabled={resettingSystem}
                sx={{ mr: 1, color: 'white', borderColor: 'white', '&:hover': { borderColor: 'white', bgcolor: 'rgba(255,255,255,0.1)' }, '&:disabled': { opacity: 0.6 } }}
              >
                {resettingSystem ? 'Resetting...' : 'Reset System'}
              </Button>
              <Button
                variant="outlined"
                color="error"
                size="small"
                startIcon={<DeleteSweepIcon />}
                onClick={handleResetMasterData}
                sx={{ mr: 1, color: 'white', borderColor: 'white', '&:hover': { borderColor: 'white', bgcolor: 'rgba(255,255,255,0.1)' } }}
              >
                Reset Master Data
              </Button>
            </>
          )}
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
