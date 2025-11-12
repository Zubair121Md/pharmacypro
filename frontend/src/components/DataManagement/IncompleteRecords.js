import React, { useEffect, useState } from 'react';
import { Box, Typography, Card, CardContent, Grid, Button, Alert, CircularProgress } from '@mui/material';
import { analyticsAPI } from '../../services/api';

function IncompleteRecords() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);

  const fetchSummary = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await analyticsAPI.getDataQuality();
      setSummary(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to fetch incomplete records summary');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const handleExport = async (format) => {
    try {
      const res = await analyticsAPI.exportDataQuality(format);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `incomplete_records.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      setError('Export failed');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Incomplete Records</Typography>
        <Box display="flex" gap={1}>
          <Button variant="outlined" onClick={() => handleExport('csv')}>Export CSV</Button>
          <Button variant="contained" onClick={() => handleExport('xlsx')}>Export Excel</Button>
        </Box>
      </Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Total Rows</Typography>
              <Typography variant="h5">{summary?.total_rows || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Valid Rows</Typography>
              <Typography variant="h5">{summary?.valid_rows || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Error Rows</Typography>
              <Typography variant="h5">{summary?.error_rows || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Valid %</Typography>
              <Typography variant="h5">{summary?.valid_percentage || 0}%</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">NIL Count</Typography>
              <Typography variant="h5">{summary?.nil_count || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">INVALID Count</Typography>
              <Typography variant="h5">{summary?.invalid_count || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      <Box mt={2}>
        <Alert severity="info">
          {(summary?.notes?.nil) || ''} {(summary?.notes?.invalid) || ''}
        </Alert>
      </Box>
    </Box>
  );
}

export default IncompleteRecords;


