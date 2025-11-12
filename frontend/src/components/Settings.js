import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Avatar,
  Badge,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Palette as PaletteIcon,
  Language as LanguageIcon,
  Storage as StorageIcon,
  CloudDownload as DownloadIcon,
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import axios from 'axios';
import RoleBasedComponent from './RoleBasedComponent';

const Settings = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [selectedTab, setSelectedTab] = useState(0);
  const [settings, setSettings] = useState({
    // User preferences
    theme: 'light',
    language: 'en',
    notifications: true,
    email_alerts: true,
    auto_refresh: true,
    refresh_interval: 30,
    
    // System settings
    data_retention: 3,
    auto_backup: true,
    backup_frequency: 'daily',
    audit_logging: true,
    
    // Display settings
    items_per_page: 25,
    date_format: 'DD/MM/YYYY',
    currency_format: 'INR',
    timezone: 'Asia/Kolkata'
  });

  const { user } = useSelector((state) => state.auth);
  const dispatch = useDispatch();
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://localhost:8000';

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/settings`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setSettings({ ...settings, ...response.data });
    } catch (err) {
      console.error('Failed to fetch settings:', err);
      // Use default settings if fetch fails
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      const token = localStorage.getItem('token');
      await axios.post(
        `${API_BASE_URL}/api/v1/settings`,
        settings,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      setSuccess('Settings saved successfully!');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const renderUserPreferences = () => (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        User Preferences
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <FormControl fullWidth margin="normal">
            <InputLabel>Theme</InputLabel>
            <Select
              value={settings.theme}
              onChange={(e) => handleSettingChange('theme', e.target.value)}
            >
              <MenuItem value="light">Light</MenuItem>
              <MenuItem value="dark">Dark</MenuItem>
              <MenuItem value="auto">Auto</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <FormControl fullWidth margin="normal">
            <InputLabel>Language</InputLabel>
            <Select
              value={settings.language}
              onChange={(e) => handleSettingChange('language', e.target.value)}
            >
              <MenuItem value="en">English</MenuItem>
              <MenuItem value="hi">Hindi</MenuItem>
              <MenuItem value="ta">Tamil</MenuItem>
              <MenuItem value="te">Telugu</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <FormControl fullWidth margin="normal">
            <InputLabel>Timezone</InputLabel>
            <Select
              value={settings.timezone}
              onChange={(e) => handleSettingChange('timezone', e.target.value)}
            >
              <MenuItem value="Asia/Kolkata">Asia/Kolkata (IST)</MenuItem>
              <MenuItem value="UTC">UTC</MenuItem>
              <MenuItem value="America/New_York">America/New_York (EST)</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <FormControl fullWidth margin="normal">
            <InputLabel>Currency Format</InputLabel>
            <Select
              value={settings.currency_format}
              onChange={(e) => handleSettingChange('currency_format', e.target.value)}
            >
              <MenuItem value="INR">Indian Rupee (₹)</MenuItem>
              <MenuItem value="USD">US Dollar ($)</MenuItem>
              <MenuItem value="EUR">Euro (€)</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12}>
          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle1" gutterBottom>
            Notifications
          </Typography>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <FormControlLabel
            control={
              <Switch
                checked={settings.notifications}
                onChange={(e) => handleSettingChange('notifications', e.target.checked)}
              />
            }
            label="Enable Notifications"
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <FormControlLabel
            control={
              <Switch
                checked={settings.email_alerts}
                onChange={(e) => handleSettingChange('email_alerts', e.target.checked)}
              />
            }
            label="Email Alerts"
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <FormControlLabel
            control={
              <Switch
                checked={settings.auto_refresh}
                onChange={(e) => handleSettingChange('auto_refresh', e.target.checked)}
              />
            }
            label="Auto Refresh Data"
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Refresh Interval (seconds)"
            type="number"
            value={settings.refresh_interval}
            onChange={(e) => handleSettingChange('refresh_interval', parseInt(e.target.value))}
            disabled={!settings.auto_refresh}
            margin="normal"
          />
        </Grid>
      </Grid>
    </Paper>
  );

  const renderDisplaySettings = () => (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Display Settings
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Items Per Page"
            type="number"
            value={settings.items_per_page}
            onChange={(e) => handleSettingChange('items_per_page', parseInt(e.target.value))}
            margin="normal"
            inputProps={{ min: 10, max: 100 }}
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <FormControl fullWidth margin="normal">
            <InputLabel>Date Format</InputLabel>
            <Select
              value={settings.date_format}
              onChange={(e) => handleSettingChange('date_format', e.target.value)}
            >
              <MenuItem value="DD/MM/YYYY">DD/MM/YYYY</MenuItem>
              <MenuItem value="MM/DD/YYYY">MM/DD/YYYY</MenuItem>
              <MenuItem value="YYYY-MM-DD">YYYY-MM-DD</MenuItem>
            </Select>
          </FormControl>
        </Grid>
      </Grid>
    </Paper>
  );

  const renderSystemSettings = () => (
    <RoleBasedComponent allowedRoles={['admin', 'super_admin']}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          System Settings
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Data Retention (years)"
              type="number"
              value={settings.data_retention}
              onChange={(e) => handleSettingChange('data_retention', parseInt(e.target.value))}
              margin="normal"
              inputProps={{ min: 1, max: 10 }}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Backup Frequency</InputLabel>
              <Select
                value={settings.backup_frequency}
                onChange={(e) => handleSettingChange('backup_frequency', e.target.value)}
              >
                <MenuItem value="daily">Daily</MenuItem>
                <MenuItem value="weekly">Weekly</MenuItem>
                <MenuItem value="monthly">Monthly</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" gutterBottom>
              System Features
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.auto_backup}
                  onChange={(e) => handleSettingChange('auto_backup', e.target.checked)}
                />
              }
              label="Automatic Backups"
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.audit_logging}
                  onChange={(e) => handleSettingChange('audit_logging', e.target.checked)}
                />
              }
              label="Audit Logging"
            />
          </Grid>
        </Grid>
      </Paper>
    </RoleBasedComponent>
  );

  const renderUserProfile = () => (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        User Profile
      </Typography>
      
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Avatar sx={{ width: 64, height: 64, mr: 2 }}>
          {user?.username?.charAt(0).toUpperCase()}
        </Avatar>
        <Box>
          <Typography variant="h6">{user?.username}</Typography>
          <Typography variant="body2" color="text.secondary">{user?.email}</Typography>
          <Chip 
            label={user?.role?.replace('_', ' ').toUpperCase()} 
            color="primary" 
            size="small" 
            sx={{ mt: 1 }}
          />
        </Box>
      </Box>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Username"
            value={user?.username || ''}
            disabled
            margin="normal"
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Email"
            value={user?.email || ''}
            disabled
            margin="normal"
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Role"
            value={user?.role?.replace('_', ' ').toUpperCase() || ''}
            disabled
            margin="normal"
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Area"
            value={user?.area || 'All Areas'}
            disabled
            margin="normal"
          />
        </Grid>
      </Grid>
    </Paper>
  );

  const renderDataManagement = () => (
    <RoleBasedComponent allowedRoles={['admin', 'super_admin']}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Data Management
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => window.open(`${API_BASE_URL}/api/v1/export/analytics-excel`, '_blank')}
            >
              Export Analytics
            </Button>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => window.open(`${API_BASE_URL}/api/v1/export/raw-data-excel`, '_blank')}
            >
              Export Raw Data
            </Button>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<UploadIcon />}
              onClick={() => window.location.href = '/upload'}
            >
              Import Data
            </Button>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              disabled
            >
              Clear Data
            </Button>
          </Grid>
        </Grid>
      </Paper>
    </RoleBasedComponent>
  );

  if (loading && !settings.theme) {
    return (
      <Container maxWidth="xl">
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Settings
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          System configuration and user preferences
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <Paper sx={{ mb: 3 }}>
        <Tabs value={selectedTab} onChange={(e, newValue) => setSelectedTab(newValue)}>
          <Tab label="Profile" />
          <Tab label="Preferences" />
          <Tab label="Display" />
          <Tab label="System" />
          <Tab label="Data" />
        </Tabs>
      </Paper>

      {selectedTab === 0 && renderUserProfile()}
      {selectedTab === 1 && renderUserPreferences()}
      {selectedTab === 2 && renderDisplaySettings()}
      {selectedTab === 3 && renderSystemSettings()}
      {selectedTab === 4 && renderDataManagement()}

      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchSettings}
          disabled={loading}
        >
          Reset
        </Button>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={saveSettings}
          disabled={loading}
        >
          {loading ? <CircularProgress size={20} /> : 'Save Settings'}
        </Button>
      </Box>
    </Container>
  );
};

export default Settings;
