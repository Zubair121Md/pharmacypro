import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Switch,
  FormControlLabel,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Avatar,
  Badge,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Person as PersonIcon,
  AdminPanelSettings as AdminIcon,
  Security as SecurityIcon,
  Settings as SettingsIcon,
  Analytics as AnalyticsIcon,
  Storage as StorageIcon,
  CloudDownload as DownloadIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import axios from 'axios';
import RoleBasedComponent from './RoleBasedComponent';

const AdminPanel = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [users, setUsers] = useState([]);
  const [systemStats, setSystemStats] = useState(null);
  const [selectedTab, setSelectedTab] = useState(0);
  const [userDialogOpen, setUserDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userForm, setUserForm] = useState({
    username: '',
    email: '',
    role: 'user',
    area: '',
    is_active: true
  });

  const { user: currentUser } = useSelector((state) => state.auth);
  const dispatch = useDispatch();
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://localhost:8000';

  useEffect(() => {
    fetchUsers();
    fetchSystemStats();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/admin/users`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setUsers(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/admin/stats`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setSystemStats(response.data);
    } catch (err) {
      console.error('Failed to fetch system stats:', err);
    }
  };

  const handleCreateUser = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API_BASE_URL}/api/v1/admin/users`,
        userForm,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setUserDialogOpen(false);
      setUserForm({ username: '', email: '', role: 'user', area: '', is_active: true });
      fetchUsers();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create user');
    }
  };

  const handleUpdateUser = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${API_BASE_URL}/api/v1/admin/users/${editingUser.id}`,
        userForm,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setUserDialogOpen(false);
      setEditingUser(null);
      setUserForm({ username: '', email: '', role: 'user', area: '', is_active: true });
      fetchUsers();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update user');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(
          `${API_BASE_URL}/api/v1/admin/users/${userId}`,
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        );
        fetchUsers();
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to delete user');
      }
    }
  };

  const handleEditUser = (user) => {
    setEditingUser(user);
    setUserForm({
      username: user.username,
      email: user.email,
      role: user.role,
      area: user.area || '',
      is_active: user.is_active
    });
    setUserDialogOpen(true);
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'super_admin': return 'error';
      case 'admin': return 'warning';
      case 'user': return 'primary';
      default: return 'default';
    }
  };

  const renderUserManagement = () => (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">User Management</Typography>
        <RoleBasedComponent allowedRoles={['super_admin', 'admin']}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setUserDialogOpen(true)}
          >
            Add User
          </Button>
        </RoleBasedComponent>
      </Box>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>User</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Area</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Avatar sx={{ width: 32, height: 32 }}>
                      {user.username.charAt(0).toUpperCase()}
                    </Avatar>
                    <Typography variant="body2">{user.username}</Typography>
                  </Box>
                </TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>
                  <Chip 
                    label={user.role.replace('_', ' ').toUpperCase()} 
                    color={getRoleColor(user.role)}
                    size="small"
                  />
                </TableCell>
                <TableCell>{user.area || 'All Areas'}</TableCell>
                <TableCell>
                  <Chip 
                    label={user.is_active ? 'Active' : 'Inactive'} 
                    color={user.is_active ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <RoleBasedComponent allowedRoles={['super_admin', 'admin']}>
                    <IconButton 
                      size="small" 
                      onClick={() => handleEditUser(user)}
                      disabled={user.id === currentUser?.id}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton 
                      size="small" 
                      color="error"
                      onClick={() => handleDeleteUser(user.id)}
                      disabled={user.id === currentUser?.id}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </RoleBasedComponent>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );

  const renderSystemStats = () => (
    <Grid container spacing={3} sx={{ mb: 3 }}>
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography color="text.secondary" gutterBottom>
                  Total Users
                </Typography>
                <Typography variant="h4">
                  {systemStats?.total_users || 0}
                </Typography>
              </Box>
              <PersonIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography color="text.secondary" gutterBottom>
                  Total Invoices
                </Typography>
                <Typography variant="h4">
                  {systemStats?.total_invoices?.toLocaleString() || 0}
                </Typography>
              </Box>
              <AnalyticsIcon sx={{ fontSize: 40, color: 'info.main' }} />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography color="text.secondary" gutterBottom>
                  Active Pharmacies
                </Typography>
                <Typography variant="h4">
                  {systemStats?.active_pharmacies || 0}
                </Typography>
              </Box>
              <StorageIcon sx={{ fontSize: 40, color: 'success.main' }} />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography color="text.secondary" gutterBottom>
                  System Health
                </Typography>
                <Typography variant="h4" color="success.main">
                  {systemStats?.system_health || 'Good'}
                </Typography>
              </Box>
              <SecurityIcon sx={{ fontSize: 40, color: 'success.main' }} />
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderSystemSettings = () => (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        System Settings
      </Typography>
      
      <List>
        <ListItem>
          <ListItemText
            primary="Data Retention Policy"
            secondary="Automatically archive data older than 3 years"
          />
          <ListItemSecondaryAction>
            <Switch checked={true} />
          </ListItemSecondaryAction>
        </ListItem>
        
        <ListItem>
          <ListItemText
            primary="Auto Backup"
            secondary="Daily automated backups enabled"
          />
          <ListItemSecondaryAction>
            <Switch checked={true} />
          </ListItemSecondaryAction>
        </ListItem>
        
        <ListItem>
          <ListItemText
            primary="Audit Logging"
            secondary="Track all user actions and system changes"
          />
          <ListItemSecondaryAction>
            <Switch checked={true} />
          </ListItemSecondaryAction>
        </ListItem>
      </List>
    </Paper>
  );

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Admin Panel
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          System administration and user management
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <RoleBasedComponent allowedRoles={['super_admin', 'admin']}>
        <Paper sx={{ mb: 3 }}>
          <Tabs value={selectedTab} onChange={(e, newValue) => setSelectedTab(newValue)}>
            <Tab label="System Overview" />
            <Tab label="User Management" />
            <Tab label="System Settings" />
          </Tabs>
        </Paper>

        {selectedTab === 0 && renderSystemStats()}
        {selectedTab === 1 && renderUserManagement()}
        {selectedTab === 2 && renderSystemSettings()}
      </RoleBasedComponent>

      <RoleBasedComponent 
        allowedRoles={['user']}
        fallback={
          <Alert severity="info">
            <Typography variant="body2">
              You need admin or super admin privileges to access this panel.
            </Typography>
          </Alert>
        }
      />

      {/* User Dialog */}
      <Dialog open={userDialogOpen} onClose={() => setUserDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingUser ? 'Edit User' : 'Create New User'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Username"
              value={userForm.username}
              onChange={(e) => setUserForm({ ...userForm, username: e.target.value })}
              margin="normal"
            />
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={userForm.email}
              onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
              margin="normal"
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Role</InputLabel>
              <Select
                value={userForm.role}
                onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}
              >
                <MenuItem value="user">User</MenuItem>
                <MenuItem value="admin">Admin</MenuItem>
                {currentUser?.role === 'super_admin' && (
                  <MenuItem value="super_admin">Super Admin</MenuItem>
                )}
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Area (Optional)"
              value={userForm.area}
              onChange={(e) => setUserForm({ ...userForm, area: e.target.value })}
              margin="normal"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={userForm.is_active}
                  onChange={(e) => setUserForm({ ...userForm, is_active: e.target.checked })}
                />
              }
              label="Active"
              sx={{ mt: 2 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUserDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={editingUser ? handleUpdateUser : handleCreateUser}
            variant="contained"
          >
            {editingUser ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AdminPanel;
