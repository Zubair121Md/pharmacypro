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
  Person as DoctorIcon,
  ContentCopy as CopyIcon,
  Add as AddIcon,
} from '@mui/icons-material';

const DoctorGenerator = () => {
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

  const generateId = (text) => {
    const normalized = normalizeText(text);
    return `DR-${normalized}`;
  };

  const handleGenerate = () => {
    if (!doctorInput.trim()) {
      setError('Please enter a doctor name to generate ID');
      return;
    }

    const generatedId = generateId(doctorInput);
    const newEntry = {
      id: Date.now(),
      originalName: doctorInput,
      generatedId,
      timestamp: new Date().toLocaleString(),
    };

    setGeneratedIds(prev => [newEntry, ...prev]);
    setError('');
    setDoctorInput('');
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
        <DoctorIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Doctor ID Generator
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Generate standardized doctor IDs with DR- prefix
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Generate New Doctor ID
              </Typography>
              <TextField
                fullWidth
                label="Doctor Name"
                value={doctorInput}
                onChange={(e) => setDoctorInput(e.target.value)}
                placeholder="e.g., DR BIBIN JACOB"
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
                disabled={!doctorInput.trim()}
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
              {doctorInput ? (
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Input: {doctorInput}
                  </Typography>
                  <Typography variant="h6" sx={{ mt: 1, fontFamily: 'monospace' }}>
                    Generated: {generateId(doctorInput)}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Enter a doctor name to see the generated ID
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
              Generated Doctor IDs
            </Typography>
            <Button variant="outlined" onClick={clearHistory}>
              Clear History
            </Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Doctor Name</TableCell>
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
                        <DoctorIcon sx={{ mr: 1, color: 'primary.main' }} />
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

export default DoctorGenerator;


