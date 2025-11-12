import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  TextField,
  Button,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import {
  LocalPharmacy as PharmacyIcon,
  Inventory as ProductIcon,
  Person as DoctorIcon,
  ContentCopy as CopyIcon,
} from '@mui/icons-material';

const MasterIdGenerator = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [pharmacyInput, setPharmacyInput] = useState('');
  const [productInput, setProductInput] = useState('');
  const [doctorInput, setDoctorInput] = useState('');
  const [generatedIds, setGeneratedIds] = useState([]);
  const [error, setError] = useState('');

  const normalizeText = (text) => {
    if (!text) return '';
    return text
      .toUpperCase()
      .replace(/[^A-Z0-9]/g, '')
      .substring(0, 8)
      .padEnd(8, '-');
  };

  const generateId = (text, prefix) => {
    if (prefix === 'PA-') {
      // Match backend/script: split on first comma, use remainder as location
      const raw = (text || '').trim();
      const commaIdx = raw.indexOf(',');
      let facility = raw;
      let locationRemainder = '';
      if (commaIdx !== -1) {
        facility = raw.slice(0, commaIdx);
        locationRemainder = raw.slice(commaIdx + 1);
      } else {
        locationRemainder = 'Not Specified';
      }
      const facilityCode = (facility || '').replace(/[^A-Za-z0-9\.]/g, '').toUpperCase().slice(0, 10);
      const locClean = (locationRemainder || '').replace(/[^A-Za-z0-9\.]/g, '').toUpperCase();
      let locationCode = locClean ? locClean.slice(-10) : '';
      if (locationCode && locationCode.length < 10) {
        locationCode = locationCode.padEnd(10, '_');
      }
      return locationCode ? `${facilityCode}-${locationCode}` : facilityCode;
    }
    const normalized = normalizeText(text);
    return `${prefix}${normalized}`;
  };

  const handleGenerate = (type, input) => {
    if (!input.trim()) {
      setError('Please enter a name to generate ID');
      return;
    }

    let prefix = '';
    let icon = null;
    let category = '';

    switch (type) {
      case 'pharmacy':
        prefix = 'PA-';
        icon = <PharmacyIcon />;
        category = 'Pharmacy';
        break;
      case 'product':
        prefix = 'PX-';
        icon = <ProductIcon />;
        category = 'Product';
        break;
      case 'doctor':
        prefix = 'DR-';
        icon = <DoctorIcon />;
        category = 'Doctor';
        break;
      default:
        return;
    }

    const generatedId = generateId(input, prefix);
    const newEntry = {
      id: Date.now(),
      originalName: input,
      generatedId,
      category,
      icon,
      timestamp: new Date().toLocaleString(),
    };

    setGeneratedIds(prev => [newEntry, ...prev]);
    setError('');
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const clearHistory = () => {
    setGeneratedIds([]);
  };

  const TabPanel = ({ children, value, index, ...other }) => (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`generator-tabpanel-${index}`}
      aria-labelledby={`generator-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );

  const a11yProps = (index) => ({
    id: `generator-tab-${index}`,
    'aria-controls': `generator-tabpanel-${index}`,
  });

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" gutterBottom>
        Master ID Generator
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Generate standardized IDs for pharmacies, products, and doctors
      </Typography>

      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={activeTab}
            onChange={(e, newValue) => setActiveTab(newValue)}
            aria-label="generator tabs"
          >
            <Tab
              icon={<PharmacyIcon />}
              label="Pharmacy"
              {...a11yProps(0)}
            />
            <Tab
              icon={<ProductIcon />}
              label="Products"
              {...a11yProps(1)}
            />
            <Tab
              icon={<DoctorIcon />}
              label="Doctor"
              {...a11yProps(2)}
            />
          </Tabs>
        </Box>

        {error && (
          <Alert severity="error" sx={{ m: 2 }}>
            {error}
          </Alert>
        )}

        <TabPanel value={activeTab} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Generate Pharmacy ID
                  </Typography>
                  <TextField
                    fullWidth
                    label="Pharmacy Name"
                    value={pharmacyInput}
                    onChange={(e) => setPharmacyInput(e.target.value)}
                    placeholder="e.g., ACE CARE PHARMACY-PULPALLY"
                    sx={{ mb: 2 }}
                  />
                  <Button
                    variant="contained"
                    onClick={() => handleGenerate('pharmacy', pharmacyInput)}
                    fullWidth
                  >
                    Generate Pharmacy ID
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Preview
                  </Typography>
                  {pharmacyInput && (
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Input: {pharmacyInput}
                      </Typography>
                      <Typography variant="h6" sx={{ mt: 1 }}>
                        Generated: {generateId(pharmacyInput, 'PA-')}
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Generate Product ID
                  </Typography>
                  <TextField
                    fullWidth
                    label="Product Name"
                    value={productInput}
                    onChange={(e) => setProductInput(e.target.value)}
                    placeholder="e.g., BRETHNOL SYP"
                    sx={{ mb: 2 }}
                  />
                  <Button
                    variant="contained"
                    onClick={() => handleGenerate('product', productInput)}
                    fullWidth
                  >
                    Generate Product ID
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Preview
                  </Typography>
                  {productInput && (
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Input: {productInput}
                      </Typography>
                      <Typography variant="h6" sx={{ mt: 1 }}>
                        Generated: {generateId(productInput, 'PX-')}
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Generate Doctor ID
                  </Typography>
                  <TextField
                    fullWidth
                    label="Doctor Name"
                    value={doctorInput}
                    onChange={(e) => setDoctorInput(e.target.value)}
                    placeholder="e.g., DR BIBIN JACOB"
                    sx={{ mb: 2 }}
                  />
                  <Button
                    variant="contained"
                    onClick={() => handleGenerate('doctor', doctorInput)}
                    fullWidth
                  >
                    Generate Doctor ID
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Preview
                  </Typography>
                  {doctorInput && (
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Input: {doctorInput}
                      </Typography>
                      <Typography variant="h6" sx={{ mt: 1 }}>
                        Generated: {generateId(doctorInput, 'DR-')}
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      {generatedIds.length > 0 && (
        <Paper sx={{ mt: 3 }}>
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              Generated IDs History
            </Typography>
            <Button variant="outlined" onClick={clearHistory}>
              Clear History
            </Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Category</TableCell>
                  <TableCell>Original Name</TableCell>
                  <TableCell>Generated ID</TableCell>
                  <TableCell>Generated At</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {generatedIds.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell>
                      <Chip
                        icon={entry.icon}
                        label={entry.category}
                        color="primary"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>{entry.originalName}</TableCell>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {entry.generatedId}
                      </Typography>
                    </TableCell>
                    <TableCell>{entry.timestamp}</TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        startIcon={<CopyIcon />}
                        onClick={() => copyToClipboard(entry.generatedId)}
                      >
                        Copy
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}
    </Box>
  );
};

export default MasterIdGenerator;
