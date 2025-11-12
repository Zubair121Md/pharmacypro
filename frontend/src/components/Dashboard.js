import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Box,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Analytics as AnalyticsIcon,
  AdminPanelSettings as AdminIcon,
  Settings as SettingsIcon,
  TrendingUp as TrendingUpIcon,
  Store as StoreIcon,
  AttachMoney as MoneyIcon,
  Assessment as ReportIcon,
} from '@mui/icons-material';
import axios from 'axios';

const Dashboard = () => {
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://localhost:8000';

  useEffect(() => {
    fetchSummaryData();
  }, []);

  const fetchSummaryData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/analytics/summary`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setSummaryData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch summary data');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    if (amount === "***") return "***";
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount);
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Welcome to the Pharmacy Revenue Management System
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {typeof error === 'string' ? error : JSON.stringify(error)}
        </Alert>
      )}

      {/* Summary Cards */}
      {summaryData && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%', background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="white" gutterBottom>
                      Total Revenue
                    </Typography>
                    <Typography variant="h4" sx={{ color: 'white', fontWeight: 'bold' }}>
                      {formatCurrency(summaryData.summary_metrics?.total_revenue || 0)}
                    </Typography>
                    {summaryData.summary_metrics?.growth_rate !== 0 && (
                      <Chip 
                        label={`${summaryData.summary_metrics.growth_rate > 0 ? '+' : ''}${summaryData.summary_metrics.growth_rate.toFixed(1)}%`}
                        size="small"
                        sx={{ 
                          mt: 1, 
                          backgroundColor: summaryData.summary_metrics.growth_rate > 0 ? 'rgba(76, 175, 80, 0.8)' : 'rgba(244, 67, 54, 0.8)',
                          color: 'white'
                        }}
                      />
                    )}
                  </Box>
                  <MoneyIcon sx={{ fontSize: 40, color: 'rgba(255,255,255,0.8)' }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%', background: 'linear-gradient(45deg, #FF9800 30%, #FFB74D 90%)' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="white" gutterBottom>
                      Total Orders
                    </Typography>
                    <Typography variant="h4" sx={{ color: 'white', fontWeight: 'bold' }}>
                      {summaryData.summary_metrics?.total_invoices?.toLocaleString() || 0}
                    </Typography>
                  </Box>
                  <StoreIcon sx={{ fontSize: 40, color: 'rgba(255,255,255,0.8)' }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%', background: 'linear-gradient(45deg, #4CAF50 30%, #81C784 90%)' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="white" gutterBottom>
                      Active Pharmacies
                    </Typography>
                    <Typography variant="h4" sx={{ color: 'white', fontWeight: 'bold' }}>
                      {summaryData.summary_metrics?.total_pharmacies || 0}
                    </Typography>
                  </Box>
                  <TrendingUpIcon sx={{ fontSize: 40, color: 'rgba(255,255,255,0.8)' }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%', background: 'linear-gradient(45deg, #9C27B0 30%, #BA68C8 90%)' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="white" gutterBottom>
                      Avg. Order Value
                    </Typography>
                    <Typography variant="h4" sx={{ color: 'white', fontWeight: 'bold' }}>
                      {formatCurrency(summaryData.summary_metrics?.average_order_value || 0)}
                    </Typography>
                  </Box>
                  <ReportIcon sx={{ fontSize: 40, color: 'rgba(255,255,255,0.8)' }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
          <CircularProgress />
        </Box>
      )}

      <Grid container spacing={3}>
        {/* File Upload Card */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <UploadIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" component="h2">
                  File Upload
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Upload master data and invoice files for processing and ID generation.
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" href="/upload">
                Go to Upload
              </Button>
            </CardActions>
          </Card>
        </Grid>

        {/* Analytics Card */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AnalyticsIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" component="h2">
                  Analytics
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                View revenue analytics, charts, and comprehensive reports.
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" href="/analytics">
                View Analytics
              </Button>
            </CardActions>
          </Card>
        </Grid>

        {/* Admin Panel Card */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AdminIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" component="h2">
                  Admin Panel
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Manage users, system settings, and administrative functions.
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" href="/admin">
                Go to Admin
              </Button>
            </CardActions>
          </Card>
        </Grid>

        {/* Settings Card */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <SettingsIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" component="h2">
                  Settings
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Configure system settings, preferences, and user profile.
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" href="/settings">
                Go to Settings
              </Button>
            </CardActions>
          </Card>
        </Grid>

        {/* System Status Card */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Phase 1: Project Foundation & Setup - ✅ Complete
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Phase 2: Core ID Generation System - 🚧 In Progress
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Phase 3: Data Processing & Matching - ⏳ Pending
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Phase 4: Analytics & Visualization - ⏳ Pending
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;
