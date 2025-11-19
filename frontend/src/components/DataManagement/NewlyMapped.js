import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Chip,
  Alert,
  CircularProgress,
  TextField,
  InputAdornment,
  IconButton,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Autocomplete,
} from '@mui/material';
import {
  Refresh,
  Search,
  Clear,
  Visibility,
  CheckCircle,
  Edit,
  Delete,
} from '@mui/icons-material';
import { newlyMappedAPI, unmatchedAPI } from '../../services/api';

function NewlyMapped() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [masterPharmacies, setMasterPharmacies] = useState([]);
  const [pharmacySearchQuery, setPharmacySearchQuery] = useState('');
  const [filteredPharmacies, setFilteredPharmacies] = useState([]);
  const [editData, setEditData] = useState({ master_pharmacy_id: '' });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchNewlyMappedRecords();
  }, []);

  const fetchNewlyMappedRecords = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await newlyMappedAPI.getNewlyMappedRecords();
      setRecords(response.data || []);
    } catch (error) {
      setError('Failed to fetch newly mapped records');
      console.error('Error fetching newly mapped records:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = (record) => {
    setSelectedRecord(record);
    setDetailDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDetailDialogOpen(false);
    setSelectedRecord(null);
  };

  const fetchMasterPharmacies = async () => {
    try {
      const response = await unmatchedAPI.getMasterPharmacies();
      setMasterPharmacies(response.data || []);
      setFilteredPharmacies(response.data || []);
    } catch (error) {
      console.error('Failed to fetch master pharmacies:', error);
    }
  };

  useEffect(() => {
    if (editDialogOpen) {
      fetchMasterPharmacies();
    }
  }, [editDialogOpen]);

  useEffect(() => {
    if (editDialogOpen && pharmacySearchQuery !== undefined) {
      if (pharmacySearchQuery.trim() === '') {
        setFilteredPharmacies(masterPharmacies);
      } else {
        const filtered = masterPharmacies.filter(pharmacy =>
          (pharmacy.pharmacy_name || '').toLowerCase().includes(pharmacySearchQuery.toLowerCase()) ||
          (pharmacy.pharmacy_id || '').toLowerCase().includes(pharmacySearchQuery.toLowerCase())
        );
        setFilteredPharmacies(filtered);
      }
    }
  }, [pharmacySearchQuery, masterPharmacies, editDialogOpen]);

  const handleEdit = (record) => {
    setSelectedRecord(record);
    setEditData({
      master_pharmacy_id: record.mapped_to_pharmacy_id || '',
    });
    setPharmacySearchQuery('');
    setEditDialogOpen(true);
  };

  const handleCloseEditDialog = () => {
    setEditDialogOpen(false);
    setSelectedRecord(null);
    setEditData({ master_pharmacy_id: '' });
    setPharmacySearchQuery('');
    setError(null);
  };

  const handleSaveEdit = async () => {
    if (!editData.master_pharmacy_id) {
      setError('Please select a master pharmacy');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await newlyMappedAPI.updateMapping(selectedRecord.id, editData.master_pharmacy_id);
      setSuccess('Mapping updated successfully!');
      setEditDialogOpen(false);
      fetchNewlyMappedRecords();
      setTimeout(() => setSuccess(null), 3000);
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to update mapping');
      console.error('Error updating mapping:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = (record) => {
    setSelectedRecord(record);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    setSaving(true);
    setError(null);
    try {
      await newlyMappedAPI.deleteMapping(selectedRecord.id);
      setSuccess('Mapping deleted successfully! Record reverted to unmatched.');
      setDeleteDialogOpen(false);
      fetchNewlyMappedRecords();
      setTimeout(() => setSuccess(null), 3000);
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to delete mapping');
      console.error('Error deleting mapping:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleCloseDeleteDialog = () => {
    setDeleteDialogOpen(false);
    setSelectedRecord(null);
    setError(null);
  };

  const filteredRecords = records.filter(record => {
    const searchLower = searchTerm.toLowerCase();
    return (
      (record.original_pharmacy_name || '').toLowerCase().includes(searchLower) ||
      (record.generated_id || '').toLowerCase().includes(searchLower) ||
      (record.mapped_to_pharmacy_name || '').toLowerCase().includes(searchLower) ||
      (record.mapped_to_pharmacy_id || '').toLowerCase().includes(searchLower) ||
      (record.product || '').toLowerCase().includes(searchLower)
    );
  });

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  if (loading && !records.length) {
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
          Newly Mapped Records
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={fetchNewlyMappedRecords}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      <Typography variant="body1" color="text.secondary" gutterBottom>
        View records that were recently mapped manually from unmatched records.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Box display="flex" gap={2} mb={2} alignItems="center">
            <TextField
              size="small"
              fullWidth
              placeholder="Search by pharmacy name, ID, product..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search sx={{ color: 'text.secondary' }} />
                  </InputAdornment>
                ),
                endAdornment: searchTerm && (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="clear search"
                      onClick={() => setSearchTerm('')}
                      edge="end"
                      size="small"
                    >
                      <Clear />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Box>

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Original Pharmacy</strong></TableCell>
                  <TableCell><strong>Generated ID</strong></TableCell>
                  <TableCell><strong>Mapped To</strong></TableCell>
                  <TableCell><strong>Product</strong></TableCell>
                  <TableCell align="right"><strong>Quantity</strong></TableCell>
                  <TableCell align="right"><strong>Amount</strong></TableCell>
                  <TableCell><strong>Mapped Date</strong></TableCell>
                  <TableCell><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredRecords.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      <Box py={4}>
                        <Typography variant="body1" color="text.secondary">
                          {searchTerm
                            ? 'No records found matching your search'
                            : 'No newly mapped records found'}
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredRecords.map((record) => (
                    <TableRow key={record.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {record.original_pharmacy_name || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={record.generated_id || '-'}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {record.mapped_to_pharmacy_name || '-'}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            ID: {record.mapped_to_pharmacy_id || '-'}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>{record.product || '-'}</TableCell>
                      <TableCell align="right">
                        {record.quantity ? Number(record.quantity).toLocaleString() : '-'}
                      </TableCell>
                      <TableCell align="right">
                        {record.amount
                          ? `₹${Number(record.amount).toFixed(2)}`
                          : '-'}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDate(record.mapped_at || record.created_at)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => handleViewDetails(record)}
                            title="View Details"
                          >
                            <Visibility />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="warning"
                            onClick={() => handleEdit(record)}
                            title="Edit Mapping"
                          >
                            <Edit />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDelete(record)}
                            title="Delete Mapping"
                          >
                            <Delete />
                          </IconButton>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {filteredRecords.length > 0 && (
            <Box mt={2}>
              <Chip
                label={`Showing ${filteredRecords.length} of ${records.length} mapped records`}
                color="primary"
                variant="outlined"
              />
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <CheckCircle color="success" />
            <Typography variant="h6">Mapping Details</Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedRecord && (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  ORIGINAL UNMATCHED RECORD
                </Typography>
                <Card variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Pharmacy Name:
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {selectedRecord.original_pharmacy_name || '-'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Generated ID:
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {selectedRecord.generated_id || '-'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Product:
                      </Typography>
                      <Typography variant="body1">
                        {selectedRecord.product || '-'}
                      </Typography>
                    </Grid>
                    <Grid item xs={3}>
                      <Typography variant="body2" color="text.secondary">
                        Quantity:
                      </Typography>
                      <Typography variant="body1">
                        {selectedRecord.quantity || '-'}
                      </Typography>
                    </Grid>
                    <Grid item xs={3}>
                      <Typography variant="body2" color="text.secondary">
                        Amount:
                      </Typography>
                      <Typography variant="body1">
                        {selectedRecord.amount
                          ? `₹${Number(selectedRecord.amount).toFixed(2)}`
                          : '-'}
                      </Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">
                        Created At:
                      </Typography>
                      <Typography variant="body1">
                        {formatDate(selectedRecord.created_at)}
                      </Typography>
                    </Grid>
                  </Grid>
                </Card>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom sx={{ mt: 2 }}>
                  MAPPED TO
                </Typography>
                <Card variant="outlined" sx={{ p: 2, bgcolor: 'rgba(76, 175, 80, 0.1)' }}>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Master Pharmacy Name:
                      </Typography>
                      <Typography variant="body1" fontWeight="bold" color="success.dark">
                        {selectedRecord.mapped_to_pharmacy_name || '-'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Master Pharmacy ID:
                      </Typography>
                      <Typography variant="body1" fontWeight="bold" color="success.dark">
                        {selectedRecord.mapped_to_pharmacy_id || '-'}
                      </Typography>
                    </Grid>
                    {selectedRecord.mapped_to_product_name && (
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          Product:
                        </Typography>
                        <Typography variant="body1">
                          {selectedRecord.mapped_to_product_name}
                        </Typography>
                      </Grid>
                    )}
                    {selectedRecord.mapped_to_doctor_name && (
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          Doctor:
                        </Typography>
                        <Typography variant="body1">
                          {selectedRecord.mapped_to_doctor_name}
                        </Typography>
                      </Grid>
                    )}
                    {selectedRecord.mapped_to_rep_name && (
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          Rep:
                        </Typography>
                        <Typography variant="body1">
                          {selectedRecord.mapped_to_rep_name}
                        </Typography>
                      </Grid>
                    )}
                    {selectedRecord.mapped_to_hq && (
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          HQ:
                        </Typography>
                        <Typography variant="body1">
                          {selectedRecord.mapped_to_hq}
                        </Typography>
                      </Grid>
                    )}
                    {selectedRecord.mapped_to_area && (
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          Area:
                        </Typography>
                        <Typography variant="body1">
                          {selectedRecord.mapped_to_area}
                        </Typography>
                      </Grid>
                    )}
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">
                        Mapped At:
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {formatDate(selectedRecord.mapped_at || selectedRecord.created_at)}
                      </Typography>
                    </Grid>
                  </Grid>
                </Card>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Mapping Dialog */}
      <Dialog open={editDialogOpen} onClose={handleCloseEditDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          Edit Mapping
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          {selectedRecord && (
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Original Pharmacy: <strong>{selectedRecord.original_pharmacy_name}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Generated ID: <strong>{selectedRecord.generated_id}</strong>
              </Typography>
              
              <Autocomplete
                fullWidth
                sx={{ mt: 2 }}
                options={filteredPharmacies}
                getOptionLabel={(option) => `${option.pharmacy_name} (${option.pharmacy_id})`}
                value={masterPharmacies.find(p => p.pharmacy_id === editData.master_pharmacy_id) || null}
                onChange={(event, newValue) => {
                  setEditData({
                    master_pharmacy_id: newValue ? newValue.pharmacy_id : '',
                  });
                }}
                onInputChange={(event, newInputValue) => {
                  setPharmacySearchQuery(newInputValue);
                }}
                inputValue={pharmacySearchQuery}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Select Master Pharmacy"
                    placeholder="Type to search pharmacy name or ID..."
                    variant="outlined"
                  />
                )}
                noOptionsText="No pharmacies found"
                loading={masterPharmacies.length === 0}
                filterOptions={(options, state) => {
                  return options;
                }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseEditDialog} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleSaveEdit} variant="contained" disabled={saving}>
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={handleCloseDeleteDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          Delete Mapping?
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          {selectedRecord && (
            <Box>
              <Alert severity="warning" sx={{ mb: 2 }}>
                This will revert the record back to unmatched status. Are you sure you want to continue?
              </Alert>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Original Pharmacy: <strong>{selectedRecord.original_pharmacy_name}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Currently Mapped To: <strong>{selectedRecord.mapped_to_pharmacy_name}</strong>
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDialog} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleConfirmDelete} variant="contained" color="error" disabled={saving}>
            {saving ? 'Deleting...' : 'Delete Mapping'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default NewlyMapped;

