import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
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
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  LocalPharmacy as PharmacyIcon,
  ContentCopy as CopyIcon,
  Add as AddIcon,
} from '@mui/icons-material';

const PharmacyGenerator = () => {
  const [pharmacyInput, setPharmacyInput] = useState('');
  const [generatedIds, setGeneratedIds] = useState([]);
  const [error, setError] = useState('');

  const generateId = (text) => {
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
  };

  const handleGenerate = () => {
    if (!pharmacyInput.trim()) {
      setError('Please enter a pharmacy name to generate ID');
      return;
    }

    const generatedId = generateId(pharmacyInput);
    const newEntry = {
      id: Date.now(),
      originalName: pharmacyInput,
      generatedId,
      timestamp: new Date().toLocaleString(),
    };

    setGeneratedIds(prev => [newEntry, ...prev]);
    setError('');
    setPharmacyInput('');
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const clearHistory = () => {
    setGeneratedIds([]);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" gutterBottom>
        <PharmacyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Pharmacy ID Generator
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Generate standardized pharmacy IDs with PA- prefix
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Generate New Pharmacy ID
              </Typography>
              <TextField
                fullWidth
                label="Pharmacy Name"
                value={pharmacyInput}
                onChange={(e) => setPharmacyInput(e.target.value)}
                placeholder="e.g., ACE CARE PHARMACY-PULPALLY"
                sx={{ mb: 2 }}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleGenerate();
                  }
                }}
              />
              <Button
                variant="contained"
                onClick={handleGenerate}
                fullWidth
                startIcon={<AddIcon />}
                disabled={!pharmacyInput.trim()}
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
              {pharmacyInput ? (
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Input: {pharmacyInput}
                  </Typography>
                  <Typography variant="h6" sx={{ mt: 1, fontFamily: 'monospace' }}>
                    Generated: {generateId(pharmacyInput)}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Enter a pharmacy name to see the generated ID
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {generatedIds.length > 0 && (
        <Paper sx={{ mt: 3 }}>
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              Generated Pharmacy IDs
            </Typography>
            <Button variant="outlined" onClick={clearHistory}>
              Clear History
            </Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Pharmacy Name</TableCell>
                  <TableCell>Generated ID</TableCell>
                  <TableCell>Generated At</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {generatedIds.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <PharmacyIcon sx={{ mr: 1, color: 'primary.main' }} />
                        {entry.originalName}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {entry.generatedId}
                      </Typography>
                    </TableCell>
                    <TableCell>{entry.timestamp}</TableCell>
                    <TableCell>
                      <Tooltip title="Copy to clipboard">
                        <IconButton
                          size="small"
                          onClick={() => copyToClipboard(entry.generatedId)}
                        >
                          <CopyIcon />
                        </IconButton>
                      </Tooltip>
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

export default PharmacyGenerator;
