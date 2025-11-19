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
  CircularProgress,
} from '@mui/material';
import {
  Person as DoctorIcon,
  ContentCopy as CopyIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { generatorAPI } from '../../services/api';

const DoctorGenerator = () => {
  const [doctorInput, setDoctorInput] = useState('');
  const [generatedIds, setGeneratedIds] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (!doctorInput.trim()) {
      setError('Please enter a doctor name to generate ID');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await generatorAPI.generateId(doctorInput.trim(), 'doctor');
      const newEntry = {
        id: Date.now(),
        originalName: doctorInput,
        generatedId: response.data.generated_id,
        timestamp: new Date().toLocaleString(),
      };

      setGeneratedIds(prev => [newEntry, ...prev]);
      setDoctorInput('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate doctor ID');
    } finally {
      setLoading(false);
    }
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
        Generate doctor IDs with format: XXX-YYY-NNN (counter-based unique IDs)
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

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
                startIcon={loading ? <CircularProgress size={20} /> : <AddIcon />}
                disabled={!doctorInput.trim() || loading}
              >
                {loading ? 'Generating...' : 'Generate Doctor ID'}
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
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Click "Generate Doctor ID" to create unique ID
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Enter a doctor name to generate ID
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


