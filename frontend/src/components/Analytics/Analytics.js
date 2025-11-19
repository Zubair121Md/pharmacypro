import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Grid,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Area,
  AreaChart,
} from 'recharts';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import {
  fetchRevenueByPharmacy,
  fetchRevenueByDoctor,
  fetchRevenueByRep,
  fetchRevenueByHQ,
  fetchRevenueByArea,
  fetchRevenueByProduct,
  fetchMonthlyTrends,
} from '../../store/slices/analyticsSlice';
import api, { analyticsAPI } from '../../services/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

// Helper function to format currency
const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

// List View Component
function RevenueListView({ data, title, nameKey, revenueKey, color, extraColumns }) {
  if (!data || data.length === 0) {
    return (
      <Box>
        {title && (
          <Typography variant="h6" gutterBottom>
            {title}
          </Typography>
        )}
        <Typography color="text.secondary">
          No data available
        </Typography>
      </Box>
    );
  }

  const totalRevenue = data.reduce((sum, item) => sum + (item[revenueKey] || 0), 0);

  return (
    <Box>
      {title && (
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" gutterBottom>
            {title}
          </Typography>
          <Chip 
            label={`Total: ${formatCurrency(totalRevenue)}`} 
            color="primary" 
            variant="outlined"
          />
        </Box>
      )}
      
      {!title && (
        <Box display="flex" justifyContent="flex-end" alignItems="center" mb={2}>
          <Chip 
            label={`Total: ${formatCurrency(totalRevenue)}`} 
            color="primary" 
            variant="outlined"
          />
        </Box>
      )}
        
        <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                <TableCell><strong>Rank</strong></TableCell>
                <TableCell><strong>Name</strong></TableCell>
                <TableCell align="right"><strong>Revenue</strong></TableCell>
                <TableCell align="right"><strong>% of Total</strong></TableCell>
                {extraColumns?.map((col, idx) => (
                  <TableCell key={idx} align={col.align || 'left'}>
                    <strong>{col.label}</strong>
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {data.map((item, index) => {
                const percentage = totalRevenue > 0 ? ((item[revenueKey] || 0) / totalRevenue * 100) : 0;
                return (
                  <TableRow key={index} hover>
                    <TableCell>
                      <Chip 
                        label={index + 1} 
                        size="small" 
                        color="primary" 
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" noWrap>
                        {item[nameKey] || item.pharmacy_name || item.doctor_name || item.rep_name || item.hq || item.area || item.name || 'Unknown'}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight="bold" color={color}>
                        {formatCurrency(item[revenueKey] || 0)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color="text.secondary">
                        {percentage.toFixed(1)}%
                      </Typography>
                    </TableCell>
                    {extraColumns?.map((col, idx) => (
                      <TableCell key={idx} align={col.align || 'left'}>
                        <Typography variant="body2" noWrap>
                          {typeof col.value === 'function' ? col.value(item) : (item[col.key] ?? '-')}
                        </Typography>
                      </TableCell>
                    ))}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
    </Box>
  );
}

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function Analytics() {
  const dispatch = useDispatch();
  const {
    revenueByPharmacy,
    revenueByDoctor,
    revenueByRep,
    revenueByHQ,
    revenueByArea,
    revenueByProduct,
    monthlyTrends,
    loading,
    error,
  } = useSelector((state) => state.analytics);


  const [tabValue, setTabValue] = useState(0);
  const [dateRange, setDateRange] = useState('30');
  const [chartType, setChartType] = useState('bar');
  const [chartTypes, setChartTypes] = useState({
    0: 'bar', // Pharmacy
    1: 'pie', // Doctor
    2: 'bar', // Rep
    3: 'bar', // HQ
    4: 'bar', // Area
    5: 'bar', // Product
    6: 'area', // Monthly Trends
    7: 'bar', // Performance Analysis
    8: 'bar', // Data Quality
  });

  const [dataQuality, setDataQuality] = useState(null);
  const [dqLoading, setDqLoading] = useState(false);
  const [dqError, setDqError] = useState(null);

  const refreshAllAnalytics = useCallback(() => {
    dispatch(fetchRevenueByPharmacy());
    dispatch(fetchRevenueByDoctor());
    dispatch(fetchRevenueByRep());
    dispatch(fetchRevenueByHQ());
    dispatch(fetchRevenueByArea());
    dispatch(fetchRevenueByProduct());
    dispatch(fetchMonthlyTrends());
  }, [dispatch]);

  useEffect(() => {
    refreshAllAnalytics();
    
    // Listen for analytics data updates (e.g., after split rule changes)
    const handleAnalyticsUpdate = () => {
      console.log('Analytics data updated, refreshing analytics...');
      refreshAllAnalytics();
    };
    
    window.addEventListener('analyticsDataUpdated', handleAnalyticsUpdate);
    
    return () => {
      window.removeEventListener('analyticsDataUpdated', handleAnalyticsUpdate);
    };
  }, [refreshAllAnalytics]);

  useEffect(() => {
    // Load Data Quality
    (async () => {
      try {
        setDqLoading(true);
        setDqError(null);
        const res = await analyticsAPI.getDataQuality();
        setDataQuality(res.data);
      } catch (e) {
        console.error('Data quality error:', e);
        setDqError(e.response?.data?.detail || e.message || 'Failed to fetch data quality');
      } finally {
        setDqLoading(false);
      }
    })();
  }, [dispatch]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setChartType(chartTypes[newValue] || 'bar');
  };

  const handleChartTypeChange = (event) => {
    const newChartType = event.target.value;
    setChartType(newChartType);
    setChartTypes(prev => ({
      ...prev,
      [tabValue]: newChartType
    }));
  };

  const handleRefresh = () => {
    refreshAllAnalytics();
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" size="small" onClick={handleRefresh}>
          Retry
        </Button>
      }>
        {typeof error === 'string' ? error : JSON.stringify(error)}
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          Analytics
        </Typography>
        <Box display="flex" gap={2}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Date Range</InputLabel>
            <Select
              value={dateRange}
              label="Date Range"
              onChange={(e) => setDateRange(e.target.value)}
            >
              <MenuItem value="7">Last 7 days</MenuItem>
              <MenuItem value="30">Last 30 days</MenuItem>
              <MenuItem value="90">Last 90 days</MenuItem>
              <MenuItem value="365">Last year</MenuItem>
            </Select>
          </FormControl>
          <Button variant="outlined" onClick={handleRefresh}>
            Refresh
          </Button>
        </Box>
      </Box>

      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Revenue by Pharmacy" />
            <Tab label="Revenue by Doctor" />
            <Tab label="Revenue by Rep" />
            <Tab label="Revenue by HQ" />
            <Tab label="Revenue by Area" />
            <Tab label="Revenue by Product" />
            <Tab label="Data Distribution" />
            <Tab label="Performance Analysis" />
            <Tab label="Data Quality" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Revenue by Pharmacy
            </Typography>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="body2" color="text.secondary">
                Top performing pharmacies by revenue
              </Typography>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Chart Type</InputLabel>
                <Select
                  value={chartType}
                  label="Chart Type"
                  onChange={handleChartTypeChange}
                >
                  <MenuItem value="bar">Bar Chart</MenuItem>
                  <MenuItem value="pie">Pie Chart</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <ResponsiveContainer width="100%" height={revenueByPharmacy?.length > 10 ? 600 : 500}>
              {chartType === 'bar' ? (
                <BarChart data={revenueByPharmacy || []} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, 'Revenue']} />
                  <Bar dataKey="revenue" fill="#8884d8" />
                </BarChart>
              ) : (
                <PieChart>
                  <Pie
                    data={[...(revenueByPharmacy || [])].sort((a,b)=>b.revenue-a.revenue).slice(0,20).concat((revenueByPharmacy||[]).length>20?[{name:'Others',revenue:[...(revenueByPharmacy||[])].sort((a,b)=>b.revenue-a.revenue).slice(20).reduce((s,i)=>s+i.revenue,0)}]:[])}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={(revenueByPharmacy?.length||0) > 20 ? 200 : (revenueByPharmacy?.length||0) > 10 ? 160 : 120}
                    fill="#8884d8"
                    dataKey="revenue"
                  >
                    {((revenueByPharmacy || []).slice(0,20)).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                    {((revenueByPharmacy||[]).length>20) && (
                      <Cell key={`cell-others`} fill={COLORS[COLORS.length-1]} />
                    )}
                  </Pie>
                  <Tooltip formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, 'Revenue']} />
                </PieChart>
              )}
            </ResponsiveContainer>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Revenue by HQ
            </Typography>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="body2" color="text.secondary">
                Revenue by headquarters
              </Typography>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Chart Type</InputLabel>
                <Select
                  value={chartType}
                  label="Chart Type"
                  onChange={handleChartTypeChange}
                >
                  <MenuItem value="bar">Bar Chart</MenuItem>
                  <MenuItem value="pie">Pie Chart</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <ResponsiveContainer width="100%" height={revenueByHQ?.length > 10 ? 600 : 500}>
              {chartType === 'bar' ? (
                <BarChart data={revenueByHQ || []} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hq" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Revenue']} />
                  <Bar dataKey="revenue" fill="#82ca9d" />
                </BarChart>
              ) : (
                <PieChart>
                  <Pie
                    data={revenueByHQ || []}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ hq, percent }) => `${hq} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#82ca9d"
                    dataKey="revenue"
                  >
                    {(revenueByHQ || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Revenue']} />
                </PieChart>
              )}
            </ResponsiveContainer>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={4}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Revenue by Area
            </Typography>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="body2" color="text.secondary">
                Revenue by geographical area
              </Typography>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Chart Type</InputLabel>
                <Select
                  value={chartType}
                  label="Chart Type"
                  onChange={handleChartTypeChange}
                >
                  <MenuItem value="bar">Bar Chart</MenuItem>
                  <MenuItem value="pie">Pie Chart</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <ResponsiveContainer width="100%" height={revenueByArea?.length > 10 ? 600 : 500}>
              {chartType === 'bar' ? (
                <BarChart data={revenueByArea || []} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="area" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Revenue']} />
                  <Bar dataKey="revenue" fill="#ffc658" />
                </BarChart>
              ) : (
                <PieChart>
                  <Pie
                    data={revenueByArea || []}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ area, percent }) => `${area} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#ffc658"
                    dataKey="revenue"
                  >
                    {(revenueByArea || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Revenue']} />
                </PieChart>
              )}
            </ResponsiveContainer>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Revenue by Doctor
            </Typography>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="body2" color="text.secondary">
                Doctor performance and revenue contribution
              </Typography>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Chart Type</InputLabel>
                <Select
                  value={chartType}
                  label="Chart Type"
                  onChange={handleChartTypeChange}
                >
                  <MenuItem value="bar">Bar Chart</MenuItem>
                  <MenuItem value="pie">Pie Chart</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <ResponsiveContainer width="100%" height={revenueByDoctor?.length > 10 ? 600 : 500}>
              {chartType === 'bar' ? (
                <BarChart data={revenueByDoctor || []} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="doctor_name" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, 'Revenue']} />
                  <Bar dataKey="revenue" fill="#8884d8" />
                </BarChart>
              ) : (
                <PieChart>
                  <Pie
                    data={[...(revenueByDoctor || [])].sort((a,b)=>b.revenue-a.revenue).slice(0,20).concat((revenueByDoctor||[]).length>20?[{doctor_name:'Others',revenue:[...(revenueByDoctor||[])].sort((a,b)=>b.revenue-a.revenue).slice(20).reduce((s,i)=>s+i.revenue,0)}]:[])}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ doctor_name, percent }) => `${doctor_name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={(revenueByDoctor?.length||0) > 20 ? 200 : (revenueByDoctor?.length||0) > 10 ? 160 : 120}
                    fill="#8884d8"
                    dataKey="revenue"
                  >
                    {((revenueByDoctor || []).slice(0,20)).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                    {((revenueByDoctor||[]).length>20) && (
                      <Cell key={`cell-others`} fill={COLORS[COLORS.length-1]} />
                    )}
                  </Pie>
                  <Tooltip formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, 'Revenue']} />
                </PieChart>
              )}
            </ResponsiveContainer>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Revenue by Rep
            </Typography>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="body2" color="text.secondary">
                Sales representative performance
              </Typography>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Chart Type</InputLabel>
                <Select
                  value={chartType}
                  label="Chart Type"
                  onChange={handleChartTypeChange}
                >
                  <MenuItem value="bar">Bar Chart</MenuItem>
                  <MenuItem value="pie">Pie Chart</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <ResponsiveContainer width="100%" height={400}>
              {chartType === 'bar' ? (
                <BarChart data={revenueByRep || []} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="rep_name" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, 'Revenue']} />
                  <Bar dataKey="revenue" fill="#00C49F" />
                </BarChart>
              ) : (
                <PieChart>
                  <Pie
                    data={revenueByRep || []}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ rep_name, percent }) => `${rep_name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#00C49F"
                    dataKey="revenue"
                  >
                    {(revenueByRep || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, 'Revenue']} />
                </PieChart>
              )}
            </ResponsiveContainer>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={5}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Revenue by Product
            </Typography>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="body2" color="text.secondary">
                Revenue by product performance
              </Typography>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Chart Type</InputLabel>
                <Select
                  value={chartType}
                  label="Chart Type"
                  onChange={handleChartTypeChange}
                >
                  <MenuItem value="bar">Bar Chart</MenuItem>
                  <MenuItem value="pie">Pie Chart</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <ResponsiveContainer width="100%" height={revenueByProduct?.length > 10 ? 600 : 500}>
              {chartType === 'bar' ? (
                <BarChart data={revenueByProduct || []} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="product_name" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Revenue']} />
                  <Bar dataKey="revenue" fill="#82ca9d" />
                </BarChart>
              ) : (
                <PieChart>
                  <Pie
                    data={revenueByProduct || []}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ product_name, percent }) => `${product_name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="revenue"
                  >
                    {(revenueByProduct || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Revenue']} />
                </PieChart>
              )}
            </ResponsiveContainer>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={6}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Data Distribution
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Revenue distribution and data insights from uploaded files
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Revenue Range Distribution
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={[
                        { range: "0-1000", count: revenueByPharmacy.filter(p => p.revenue <= 1000).length },
                        { range: "1000-5000", count: revenueByPharmacy.filter(p => p.revenue > 1000 && p.revenue <= 5000).length },
                        { range: "5000-10000", count: revenueByPharmacy.filter(p => p.revenue > 5000 && p.revenue <= 10000).length },
                        { range: "10000+", count: revenueByPharmacy.filter(p => p.revenue > 10000).length }
                      ]} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="range" />
                        <YAxis />
                        <Tooltip formatter={(value) => [value, 'Pharmacies']} />
                        <Bar dataKey="count" fill="#8884d8" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Data Summary
                    </Typography>
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2" gutterBottom>
                        <strong>Total Pharmacies:</strong> {revenueByPharmacy.length}
                      </Typography>
                      <Typography variant="body2" gutterBottom>
                        <strong>Total Doctors:</strong> {revenueByDoctor.length}
                      </Typography>
                      <Typography variant="body2" gutterBottom>
                        <strong>Total Reps:</strong> {revenueByRep.length}
                      </Typography>
                      <Typography variant="body2" gutterBottom>
                        <strong>Total HQs:</strong> {revenueByHQ.length}
                      </Typography>
                      <Typography variant="body2" gutterBottom>
                        <strong>Total Areas:</strong> {revenueByArea.length}
                      </Typography>
                      <Typography variant="body2" gutterBottom>
                        <strong>Average Revenue per Pharmacy:</strong> ₹{revenueByPharmacy.length > 0 ? (revenueByPharmacy.reduce((sum, p) => sum + p.revenue, 0) / revenueByPharmacy.length).toLocaleString('en-IN', {maximumFractionDigits: 2}) : 0}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={6}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Performance Analysis
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Comprehensive performance metrics and insights
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Top 5 Pharmacies
                    </Typography>
                    {revenueByPharmacy.slice(0, 5).map((pharmacy, index) => (
                      <Box key={index} display="flex" justifyContent="space-between" mb={1}>
                        <Typography variant="body2">{pharmacy.pharmacy_name}</Typography>
                        <Typography variant="body2" fontWeight="bold">
                          ₹{pharmacy.revenue.toLocaleString('en-IN')}
                        </Typography>
                      </Box>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Top 5 Doctors
                    </Typography>
                    {revenueByDoctor.slice(0, 5).map((doctor, index) => (
                      <Box key={index} display="flex" justifyContent="space-between" mb={1}>
                        <Typography variant="body2">{doctor.doctor_name}</Typography>
                        <Typography variant="body2" fontWeight="bold">
                          ₹{doctor.revenue.toLocaleString('en-IN')}
                        </Typography>
                      </Box>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={8}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Data Quality
            </Typography>
            {dqLoading ? (
              <Box display="flex" justifyContent="center" py={4}>
                <CircularProgress />
              </Box>
            ) : dqError ? (
              <Alert severity="error">
                {typeof dqError === 'string' ? dqError : JSON.stringify(dqError)}
              </Alert>
            ) : (
              <>
                <Grid container spacing={3} sx={{ mb: 2 }}>
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="body2" color="text.secondary">Total Rows</Typography>
                        <Typography variant="h5">{dataQuality?.total_rows || 0}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="body2" color="text.secondary">Valid Rows</Typography>
                        <Typography variant="h5">{dataQuality?.valid_rows || 0}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="body2" color="text.secondary">Error Rows</Typography>
                        <Typography variant="h5">{dataQuality?.error_rows || 0}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="body2" color="text.secondary">Valid %</Typography>
                        <Typography variant="h5">{dataQuality?.valid_percentage || 0}%</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="body2" color="text.secondary">NIL Count</Typography>
                        <Typography variant="h5">{dataQuality?.nil_count || 0}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="body2" color="text.secondary">INVALID Count</Typography>
                        <Typography variant="h5">{dataQuality?.invalid_count || 0}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
                <Box display="flex" gap={2}>
                  <Button variant="outlined" onClick={() => analyticsAPI.exportDataQuality('csv').then(res => { const url = window.URL.createObjectURL(new Blob([res.data])); const link = document.createElement('a'); link.href = url; link.setAttribute('download', 'data_quality.csv'); document.body.appendChild(link); link.click(); link.remove(); window.URL.revokeObjectURL(url); })}>Export CSV</Button>
                  <Button variant="contained" onClick={() => analyticsAPI.exportDataQuality('xlsx').then(res => { const url = window.URL.createObjectURL(new Blob([res.data])); const link = document.createElement('a'); link.href = url; link.setAttribute('download', 'data_quality.xlsx'); document.body.appendChild(link); link.click(); link.remove(); window.URL.revokeObjectURL(url); })}>Export Excel</Button>
                </Box>
                <Box mt={2}>
                  <Alert severity="info">
                    {dataQuality?.notes?.nil} {dataQuality?.notes?.invalid}
                  </Alert>
                </Box>
              </>
            )}
          </Box>
        </TabPanel>
      </Card>

      {/* Revenue Lists Section */}
      <Box mt={4}>
        <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
          Revenue Data Lists
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Detailed revenue breakdowns in table format for all categories. Click to expand each section.
        </Typography>
        
        <Box sx={{ width: '100%' }}>
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Revenue by Pharmacy</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <RevenueListView
                data={revenueByPharmacy}
                title=""
                nameKey="name"
                revenueKey="revenue"
                color="#0088FE"
                extraColumns={[
                  { label: 'Linked Product', key: 'product_name', value: (row) => row.product_name || '-' },
                  { label: 'Quantity', key: 'quantity', align: 'right', value: (row) => Number(row.quantity || 0) }
                ]}
              />
            </AccordionDetails>
          </Accordion>
          
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Revenue by Doctor</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <RevenueListView
                data={revenueByDoctor}
                title=""
                nameKey="doctor_name"
                revenueKey="revenue"
                color="#00C49F"
                extraColumns={[
                  { label: 'Product', key: 'product_name', value: (row) => row.product_name || '-' },
                  { label: 'Quantity', key: 'quantity', align: 'right', value: (row) => Number(row.quantity || 0) },
                  { label: 'Pharmacy', key: 'pharmacy_name', value: (row) => row.pharmacy_name || '-' },
                ]}
              />
            </AccordionDetails>
          </Accordion>
          
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Revenue by Representative</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <RevenueListView
                data={revenueByRep}
                title=""
                nameKey="rep_name"
                revenueKey="revenue"
                color="#FFBB28"
                extraColumns={[
                  { label: 'Pharmacy', key: 'pharmacy_name', value: (row) => row.pharmacy_name || '-' },
                  { label: 'Products', key: 'product_name', value: (row) => row.product_name || '-' },
                  { label: 'Quantity', key: 'quantity', align: 'right', value: (row) => Number(row.quantity || 0) },
                  { label: 'Doctor', key: 'doctor_name', value: (row) => row.doctor_name || '-' },
                ]}
              />
            </AccordionDetails>
          </Accordion>
          
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Revenue by HQ</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <RevenueListView
                data={revenueByHQ}
                title=""
                nameKey="hq"
                revenueKey="revenue"
                color="#FF8042"
              />
            </AccordionDetails>
          </Accordion>
          
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Revenue by Area</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <RevenueListView
                data={revenueByArea}
                title=""
                nameKey="area"
                revenueKey="revenue"
                color="#8884D8"
              />
            </AccordionDetails>
          </Accordion>
          
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Revenue by Product</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <RevenueListView
                data={revenueByProduct}
                title=""
                nameKey="product_name"
                revenueKey="revenue"
                color="#82ca9d"
              />
            </AccordionDetails>
          </Accordion>
        </Box>
      </Box>
    </Box>
  );
}

export default Analytics;
