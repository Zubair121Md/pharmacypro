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

  const normalizeText = (text, length, fromEnd = false) => {
    if (!text || !text.trim()) {
      return '_'.repeat(length);
    }
    // Remove ALL special chars (including . and ,)
    const cleaned = text.replace(/[^\w\s]/g, '').trim().toLowerCase();
    if (!cleaned) {
      return '_'.repeat(length);
    }
    // Remove spaces and slice
    const noSpaces = cleaned.replace(/\s/g, '');
    const sliceTxt = fromEnd ? noSpaces.slice(-length) : noSpaces.slice(0, length);
    return sliceTxt.toUpperCase().padEnd(length, '_');
  };

  const generateId = (text) => {
    const raw = (text || '').trim();
    if (!raw) {
      return 'INVALID';
    }
    // Use full name for both facility and location (no splitting)
    const facilityCode = normalizeText(raw, 10, false);
    const locationCode = normalizeText(raw, 10, true);
    return `${facilityCode}-${locationCode}`;
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
