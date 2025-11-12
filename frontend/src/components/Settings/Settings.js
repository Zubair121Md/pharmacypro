import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Grid,
} from '@mui/material';
import {
  Person,
  Settings as SettingsIcon,
  Security,
  DataUsage,
} from '@mui/icons-material';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function Settings() {
  const { user } = useSelector((state) => state.auth);
  const [tabValue, setTabValue] = useState(0);
  const [profileData, setProfileData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    full_name: user?.full_name || '',
  });
  const [preferences, setPreferences] = useState({
    theme: 'light',
    notifications: true,
    autoRefresh: true,
    dataRetention: '1year',
  });
  const [securitySettings, setSecuritySettings] = useState({
    twoFactor: false,
    sessionTimeout: 30,
    passwordExpiry: 90,
  });

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleProfileChange = (e) => {
    setProfileData({
      ...profileData,
      [e.target.name]: e.target.value,
    });
  };

  const handlePreferenceChange = (e) => {
    setPreferences({
      ...preferences,
      [e.target.name]: e.target.value,
    });
  };

  const handleSecurityChange = (e) => {
    setSecuritySettings({
      ...securitySettings,
      [e.target.name]: e.target.value,
    });
  };

  const handleSaveProfile = () => {
    // TODO: Implement profile update
    console.log('Saving profile:', profileData);
  };

  const handleSavePreferences = () => {
    // TODO: Implement preferences update
    console.log('Saving preferences:', preferences);
  };

  const handleSaveSecurity = () => {
    // TODO: Implement security settings update
    console.log('Saving security settings:', securitySettings);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Manage your account settings and preferences.
      </Typography>

      <Card sx={{ mt: 2 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab icon={<Person />} label="Profile" />
            <Tab icon={<SettingsIcon />} label="Preferences" />
            <Tab icon={<Security />} label="Security" />
            <Tab icon={<DataUsage />} label="Data Management" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Profile Information
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Username"
                  name="username"
                  value={profileData.username}
                  onChange={handleProfileChange}
                  disabled
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Email"
                  name="email"
                  type="email"
                  value={profileData.email}
                  onChange={handleProfileChange}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Full Name"
                  name="full_name"
                  value={profileData.full_name}
                  onChange={handleProfileChange}
                />
              </Grid>
            </Grid>
            <Box mt={3}>
              <Button variant="contained" onClick={handleSaveProfile}>
                Save Profile
              </Button>
            </Box>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box>
            <Typography variant="h6" gutterBottom>
              User Preferences
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  select
                  label="Theme"
                  name="theme"
                  value={preferences.theme}
                  onChange={handlePreferenceChange}
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="auto">Auto</option>
                </TextField>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  select
                  label="Data Retention"
                  name="dataRetention"
                  value={preferences.dataRetention}
                  onChange={handlePreferenceChange}
                >
                  <option value="6months">6 Months</option>
                  <option value="1year">1 Year</option>
                  <option value="2years">2 Years</option>
                  <option value="5years">5 Years</option>
                </TextField>
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.notifications}
                      onChange={(e) => setPreferences({
                        ...preferences,
                        notifications: e.target.checked,
                      })}
                    />
                  }
                  label="Enable Notifications"
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.autoRefresh}
                      onChange={(e) => setPreferences({
                        ...preferences,
                        autoRefresh: e.target.checked,
                      })}
                    />
                  }
                  label="Auto Refresh Data"
                />
              </Grid>
            </Grid>
            <Box mt={3}>
              <Button variant="contained" onClick={handleSavePreferences}>
                Save Preferences
              </Button>
            </Box>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Security Settings
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={securitySettings.twoFactor}
                      onChange={(e) => setSecuritySettings({
                        ...securitySettings,
                        twoFactor: e.target.checked,
                      })}
                    />
                  }
                  label="Two-Factor Authentication"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Session Timeout (minutes)"
                  name="sessionTimeout"
                  type="number"
                  value={securitySettings.sessionTimeout}
                  onChange={handleSecurityChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Password Expiry (days)"
                  name="passwordExpiry"
                  type="number"
                  value={securitySettings.passwordExpiry}
                  onChange={handleSecurityChange}
                />
              </Grid>
            </Grid>
            <Box mt={3}>
              <Button variant="contained" onClick={handleSaveSecurity}>
                Save Security Settings
              </Button>
            </Box>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Data Management
            </Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              Data management features will be available in future updates.
            </Alert>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Export Data
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Export your data in various formats
                    </Typography>
                    <Button variant="outlined" disabled>
                      Export All Data
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Clear Data
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Clear old or unnecessary data
                    </Typography>
                    <Button variant="outlined" color="warning" disabled>
                      Clear Old Data
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>
      </Card>
    </Box>
  );
}

export default Settings;

