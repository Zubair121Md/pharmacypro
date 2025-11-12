import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Divider,
  Paper,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  Receipt as ReceiptIcon,
  TrendingUp as TrendingUpIcon,
  Store as StoreIcon,
  Person as PersonIcon,
  AttachMoney as AttachMoneyIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import {
  fetchRecentUploads,
  fetchUploadDetails,
  exportUploadData,
} from '../../store/slices/recentUploadsSlice';
import { recentUploadsAPI } from '../../services/api';

function RecentUploads() {
  const dispatch = useDispatch();
  const { uploads, loading, error, selectedUpload } = useSelector((state) => state.recentUploads);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedUploadId, setSelectedUploadId] = useState(null);

  useEffect(() => {
    dispatch(fetchRecentUploads());
  }, [dispatch]);

  const handleViewDetails = (uploadId) => {
    setSelectedUploadId(uploadId);
    dispatch(fetchUploadDetails(uploadId));
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedUploadId(null);
  };

  const handleExport = async (uploadId, format = 'csv') => {
    try {
      const response = await recentUploadsAPI.exportUploadData(uploadId, format);
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `analysis_${uploadId}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
      // You could add a toast notification here
    }
  };

  const handleDelete = async (uploadId) => {
    if (window.confirm('Are you sure you want to delete this analysis? This action cannot be undone.')) {
      try {
        await recentUploadsAPI.deleteUpload(uploadId);
        // Refresh the list after successful deletion
        dispatch(fetchRecentUploads());
      } catch (error) {
        console.error('Delete failed:', error);
        // You could add a toast notification here
      }
    }
  };

  const handleRefresh = () => {
    dispatch(fetchRecentUploads());
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          Recent Uploads
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {uploads.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 8 }}>
            <ReceiptIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No uploads found
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Upload invoice and master files to see analysis results here
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {uploads.map((upload) => (
            <Grid item xs={12} md={6} lg={4} key={upload.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box display="flex" alignItems="center" mb={2}>
                    <ReceiptIcon sx={{ mr: 1, color: 'primary.main' }} />
                    <Typography variant="h6" noWrap>
                      Analysis #{upload.id}
                    </Typography>
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {new Date(upload.uploaded_at).toLocaleString()}
                  </Typography>

                  <Box sx={{ my: 2 }}>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Box display="flex" alignItems="center" mb={1}>
                          <AttachMoneyIcon sx={{ mr: 1, fontSize: 16, color: 'success.main' }} />
                          <Typography variant="body2" color="text.secondary">
                            Total Revenue
                          </Typography>
                        </Box>
                        <Typography variant="h6" color="success.main">
                          ₹{upload.total_revenue?.toLocaleString('en-IN') || '0'}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Box display="flex" alignItems="center" mb={1}>
                          <StoreIcon sx={{ mr: 1, fontSize: 16, color: 'primary.main' }} />
                          <Typography variant="body2" color="text.secondary">
                            Pharmacies
                          </Typography>
                        </Box>
                        <Typography variant="h6" color="primary.main">
                          {upload.total_pharmacies || 0}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Box display="flex" alignItems="center" mb={1}>
                          <PersonIcon sx={{ mr: 1, fontSize: 16, color: 'info.main' }} />
                          <Typography variant="body2" color="text.secondary">
                            Doctors
                          </Typography>
                        </Box>
                        <Typography variant="h6" color="info.main">
                          {upload.total_doctors || 0}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Box display="flex" alignItems="center" mb={1}>
                          <TrendingUpIcon sx={{ mr: 1, fontSize: 16, color: 'warning.main' }} />
                          <Typography variant="body2" color="text.secondary">
                            Growth Rate
                          </Typography>
                        </Box>
                        <Typography variant="h6" color="warning.main">
                          {upload.growth_rate || 0}%
                        </Typography>
                      </Grid>
                    </Grid>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Files Processed
                    </Typography>
                    <Box display="flex" flexWrap="wrap" gap={1}>
                      {upload.file_invoice && (
                        <Chip label={`Invoice: ${upload.file_invoice}`} size="small" color="primary" variant="outlined" />
                      )}
                      {upload.file_master && (
                        <Chip label={`Master: ${upload.file_master}`} size="small" color="secondary" variant="outlined" />
                      )}
                    </Box>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Processing Summary
                    </Typography>
                    <Typography variant="body2">
                      • Processed: {upload.processed_rows || 0} rows
                    </Typography>
                    <Typography variant="body2">
                      • Matched: {upload.matched_count || 0} records
                    </Typography>
                    <Typography variant="body2">
                      • Unmatched: {upload.unmatched_count || 0} records
                    </Typography>
                  </Box>
                </CardContent>

                <Box sx={{ p: 2, pt: 0 }}>
                  <Box display="flex" gap={1}>
                    <Button
                      size="small"
                      startIcon={<ViewIcon />}
                      onClick={() => handleViewDetails(upload.id)}
                      variant="outlined"
                    >
                      View Details
                    </Button>
                    <Button
                      size="small"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleExport(upload.id, 'csv')}
                      variant="outlined"
                    >
                      Export CSV
                    </Button>
                    <Button
                      size="small"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleExport(upload.id, 'xlsx')}
                      variant="outlined"
                    >
                      Export Excel
                    </Button>
                    <Button
                      size="small"
                      startIcon={<DeleteIcon />}
                      onClick={() => handleDelete(upload.id)}
                      variant="outlined"
                      color="error"
                      aria-label="Delete"
                      title="Delete"
                    >
                      🗑️
                    </Button>
                  </Box>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Upload Details Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          Upload Details - Analysis #{selectedUploadId}
        </DialogTitle>
        <DialogContent>
          {selectedUpload ? (
            <Box>
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Summary Metrics
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Revenue: ₹{selectedUpload.total_revenue?.toLocaleString('en-IN') || '0'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Pharmacies: {selectedUpload.total_pharmacies || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Doctors: {selectedUpload.total_doctors || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Growth Rate: {selectedUpload.growth_rate || 0}%
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Processing Details
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Processed Rows: {selectedUpload.processed_rows || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Matched Records: {selectedUpload.matched_count || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Unmatched Records: {selectedUpload.unmatched_count || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Status: {selectedUpload.processing_status || 'Completed'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {selectedUpload.unmatched_preview && selectedUpload.unmatched_preview.length > 0 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Unmatched Records Preview
                  </Typography>
                  <Paper sx={{ maxHeight: 200, overflow: 'auto' }}>
                    <List dense>
                      {selectedUpload.unmatched_preview.slice(0, 10).map((record, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <ReceiptIcon fontSize="small" />
                          </ListItemIcon>
                          <ListItemText
                            primary={record.pharmacy_name}
                            secondary={`Generated ID: ${record.generated_id}`}
                          />
                        </ListItem>
                      ))}
                      {selectedUpload.unmatched_preview.length > 10 && (
                        <ListItem>
                          <ListItemText
                            primary={`... and ${selectedUpload.unmatched_preview.length - 10} more`}
                            color="text.secondary"
                          />
                        </ListItem>
                      )}
                    </List>
                  </Paper>
                </Box>
              )}
            </Box>
          ) : (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Close</Button>
          {selectedUploadId && (
            <>
              <Button onClick={() => handleExport(selectedUploadId, 'csv')} variant="outlined">
                Export CSV
              </Button>
              <Button onClick={() => handleExport(selectedUploadId, 'xlsx')} variant="contained">
                Export Excel
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default RecentUploads;
