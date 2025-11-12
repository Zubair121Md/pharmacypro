import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Store as StoreIcon,
  Person as PersonIcon,
  LocalHospital as HospitalIcon,
  AttachMoney as MoneyIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import axios from 'axios';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

const Analytics = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedTab, setSelectedTab] = useState(0);
  const [selectedPeriod, setSelectedPeriod] = useState(12);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://localhost:8000';

  useEffect(() => {
    fetchDashboardData();
  }, [selectedPeriod]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/analytics/dashboard`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      setDashboardData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch analytics data');
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

  const formatPercentage = (value) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
  };

  const renderSummaryCards = () => {
    if (!dashboardData?.summary_metrics) return null;

    const metrics = dashboardData.summary_metrics;
    
    return (
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Total Revenue
                  </Typography>
                  <Typography variant="h4">
                    {formatCurrency(metrics.total_revenue)}
                  </Typography>
                  {metrics.growth_rate !== 0 && (
                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                      {metrics.growth_rate > 0 ? (
                        <TrendingUpIcon color="success" sx={{ mr: 1 }} />
                      ) : (
                        <TrendingDownIcon color="error" sx={{ mr: 1 }} />
                      )}
                      <Typography variant="body2" color={metrics.growth_rate > 0 ? 'success.main' : 'error.main'}>
                        {formatPercentage(metrics.growth_rate)}
                      </Typography>
                    </Box>
                  )}
                </Box>
                <MoneyIcon sx={{ fontSize: 40, color: 'primary.main' }} />
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
                    Total Orders
                  </Typography>
                  <Typography variant="h4">
                    {metrics.total_invoices.toLocaleString()}
                  </Typography>
                </Box>
                <StoreIcon sx={{ fontSize: 40, color: 'info.main' }} />
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
                    {metrics.total_pharmacies}
                  </Typography>
                </Box>
                <HospitalIcon sx={{ fontSize: 40, color: 'success.main' }} />
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
                    Avg. Order Value
                  </Typography>
                  <Typography variant="h4">
                    {formatCurrency(metrics.average_order_value)}
                  </Typography>
                </Box>
                <PersonIcon sx={{ fontSize: 40, color: 'warning.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  const renderMonthlyTrends = () => {
    if (!dashboardData?.monthly_revenue) return null;

    return (
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Monthly Revenue Trends</Typography>
          <FormControl size="small">
            <InputLabel>Period</InputLabel>
            <Select
              value={selectedPeriod}
              label="Period"
              onChange={(e) => setSelectedPeriod(e.target.value)}
            >
              <MenuItem value={6}>Last 6 Months</MenuItem>
              <MenuItem value={12}>Last 12 Months</MenuItem>
              <MenuItem value={24}>Last 24 Months</MenuItem>
            </Select>
          </FormControl>
        </Box>
        
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={dashboardData.monthly_revenue}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis tickFormatter={(value) => formatCurrency(value)} />
            <Tooltip formatter={(value) => formatCurrency(value)} />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="total_revenue" 
              stroke="#8884d8" 
              strokeWidth={2}
              name="Revenue"
            />
          </LineChart>
        </ResponsiveContainer>
      </Paper>
    );
  };

  const renderRevenueBreakdown = () => {
    if (!dashboardData?.pharmacy_revenue) return null;

    const topPharmacies = dashboardData.pharmacy_revenue.slice(0, 10);

    return (
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Top Pharmacies by Revenue
        </Typography>
        
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={topPharmacies}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="pharmacy_name" 
              angle={-45}
              textAnchor="end"
              height={100}
            />
            <YAxis tickFormatter={(value) => formatCurrency(value)} />
            <Tooltip formatter={(value) => formatCurrency(value)} />
            <Bar dataKey="total_revenue" fill="#8884d8" />
          </BarChart>
        </ResponsiveContainer>
      </Paper>
    );
  };

  const renderAllocationBreakdown = () => {
    if (!dashboardData?.allocation_breakdown) return null;

    const allocation = dashboardData.allocation_breakdown;
    const pieData = [
      { name: 'Doctors', value: allocation.allocation_percentages.doctors },
      { name: 'Sales Reps', value: allocation.allocation_percentages.reps }
    ];

    return (
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Revenue Allocation
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Allocation Summary
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Total Revenue: {formatCurrency(allocation.total_revenue)}
                </Typography>
              </Box>
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2">
                  Doctor Allocation: {formatCurrency(allocation.doctor_allocation)}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2">
                  Rep Allocation: {formatCurrency(allocation.rep_allocation)}
                </Typography>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Paper>
    );
  };

  const renderTopPerformers = () => {
    if (!dashboardData?.top_performers) return null;

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Top Doctors
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Doctor</TableCell>
                    <TableCell align="right">Revenue</TableCell>
                    <TableCell align="right">Orders</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {dashboardData.top_performers.top_doctors?.map((doctor, index) => (
                    <TableRow key={index}>
                      <TableCell>{doctor.doctor_name}</TableCell>
                      <TableCell align="right">{formatCurrency(doctor.total_revenue)}</TableCell>
                      <TableCell align="right">{doctor.total_orders}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Top Sales Reps
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Rep</TableCell>
                    <TableCell align="right">Revenue</TableCell>
                    <TableCell align="right">Pharmacies</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {dashboardData.top_performers.top_reps?.map((rep, index) => (
                    <TableRow key={index}>
                      <TableCell>{rep.rep_name}</TableCell>
                      <TableCell align="right">{formatCurrency(rep.total_revenue)}</TableCell>
                      <TableCell align="right">{rep.pharmacy_count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    );
  };

  if (loading) {
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
          Analytics Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Comprehensive revenue analytics and performance insights
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {dashboardData && (
        <>
          {renderSummaryCards()}
          {renderMonthlyTrends()}
          {renderRevenueBreakdown()}
          {renderAllocationBreakdown()}
          {renderTopPerformers()}
        </>
      )}

      {!dashboardData && !loading && (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h6" gutterBottom>
            No Data Available
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Upload some invoice data to see analytics
          </Typography>
          <Button variant="contained" href="/upload">
            Upload Data
          </Button>
        </Paper>
      )}
    </Container>
  );
};

export default Analytics;
