import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Alert,
  Chip,
} from '@mui/material';
import {
  DataObject,
  Assessment,
  Warning,
  CheckCircle,
} from '@mui/icons-material';

function DataManagement() {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Data Management
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Comprehensive data management features for your pharmacy revenue system.
      </Typography>

      {/* Coming Soon Alert */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Data Management Features Coming Soon
        </Typography>
        <Typography variant="body2">
          We're working on advanced data management features that will be available in future updates. 
          These will include enhanced data validation, bulk operations, data synchronization, and more.
        </Typography>
      </Alert>

      {/* Feature Overview Cards */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <DataObject sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Data Validation</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Advanced validation rules and data quality checks to ensure accuracy and consistency.
              </Typography>
              <Chip label="Coming Soon" color="primary" variant="outlined" size="small" />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Assessment sx={{ mr: 1, color: 'secondary.main' }} />
                <Typography variant="h6">Bulk Operations</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Perform bulk updates, imports, and exports across multiple records efficiently.
              </Typography>
              <Chip label="Coming Soon" color="secondary" variant="outlined" size="small" />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Warning sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="h6">Data Synchronization</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Keep your data synchronized across different systems and platforms.
              </Typography>
              <Chip label="Coming Soon" color="warning" variant="outlined" size="small" />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <CheckCircle sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6">Data Integrity</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Comprehensive data integrity checks and automated error detection.
              </Typography>
              <Chip label="Coming Soon" color="success" variant="outlined" size="small" />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Current Available Features */}
      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom>
          Currently Available
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={4}>
            <Button
              variant="outlined"
              fullWidth
              sx={{ p: 2 }}
              href="/unmatched"
            >
              <Box textAlign="center">
                <Typography variant="h6">Unmatched Records</Typography>
                <Typography variant="body2" color="text.secondary">
                  Review and manage unmatched pharmacy records
                </Typography>
              </Box>
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Button
              variant="outlined"
              fullWidth
              sx={{ p: 2 }}
              href="/incomplete"
            >
              <Box textAlign="center">
                <Typography variant="h6">Incomplete Records</Typography>
                <Typography variant="body2" color="text.secondary">
                  View data quality summaries and incomplete records
                </Typography>
              </Box>
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Button
              variant="outlined"
              fullWidth
              sx={{ p: 2 }}
              href="/recent-uploads"
            >
              <Box textAlign="center">
                <Typography variant="h6">Recent Uploads</Typography>
                <Typography variant="body2" color="text.secondary">
                  Track recent file uploads and processing history
                </Typography>
              </Box>
            </Button>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
}

export default DataManagement;
