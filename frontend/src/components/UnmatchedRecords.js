import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Autocomplete,
  Alert,
  CircularProgress,
  Pagination,
  Grid,
  Card,
  CardContent,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Search as SearchIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Visibility as ViewIcon,
  Map as MapIcon,
} from '@mui/icons-material';
import axios from 'axios';
import { unmatchedAPI } from '../services/api';

const UnmatchedRecords = () => {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [mapDialogOpen, setMapDialogOpen] = useState(false);
  const [masterPharmacies, setMasterPharmacies] = useState([]);
  const [selectedMasterPharmacy, setSelectedMasterPharmacy] = useState(null);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://localhost:8000';

  useEffect(() => {
    fetchRecords();
    fetchMasterPharmacies();
  }, [page, statusFilter]);

  const fetchRecords = async () => {
    try {
      setLoading(true);
      const response = await unmatchedAPI.getUnmatchedRecords();
      setRecords(response.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch records');
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      const res = await unmatchedAPI.exportCSV();
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'text/csv' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'unmatched_records.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.detail || 'Export failed');
    }
  };

  const handleExportExcel = async () => {
    try {
      const res = await unmatchedAPI.exportExcel();
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'unmatched_records.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.detail || 'Export failed');
    }
  };

  const fetchMasterPharmacies = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/unmatched/master-pharmacies`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setMasterPharmacies(response.data);
    } catch (err) {
      console.error('Failed to fetch master pharmacies:', err);
    }
  };

  const handleMapRecord = async (recordId, masterPharmacyId) => {
    try {
      await unmatchedAPI.mapRecord(recordId, masterPharmacyId);
      
      setMapDialogOpen(false);
      setSelectedRecord(null);
      setSelectedMasterPharmacy(null);
      fetchRecords();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to map record');
    }
  };

  const handleIgnoreRecord = async (recordId) => {
    try {
      await unmatchedAPI.ignoreRecord(recordId);
      fetchRecords();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to ignore record');
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      fetchRecords();
      return;
    }

    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/unmatched/search`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { query: searchQuery }
        }
      );
      setRecords(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'warning';
      case 'mapped': return 'success';
      case 'ignored': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return <ViewIcon />;
      case 'mapped': return <CheckIcon />;
      case 'ignored': return <CancelIcon />;
      default: return null;
    }
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Unmatched Records Management
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Review and map unmatched pharmacy records to master data
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Filters and Search */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              select
              fullWidth
              label="Status Filter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              SelectProps={{ native: true }}
            >
              <option value="pending">Pending</option>
              <option value="mapped">Mapped</option>
              <option value="ignored">Ignored</option>
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6} md={6}>
            <TextField
              fullWidth
              label="Search pharmacy names"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              variant="contained"
              startIcon={<SearchIcon />}
              onClick={handleSearch}
              fullWidth
            >
              Search
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Records Table */}
      <Paper>
        <Box sx={{ p: 2, display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
          <Button variant="outlined" onClick={handleExportCSV}>Export CSV</Button>
          <Button variant="outlined" onClick={handleExportExcel}>Export Excel</Button>
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Pharmacy Name</TableCell>
                <TableCell>Generated ID</TableCell>
                <TableCell>Product</TableCell>
                <TableCell align="right">Quantity</TableCell>
                <TableCell align="right">Revenue</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Mapped To</TableCell>
                <TableCell>Created At</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={9} align="center">
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : records.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} align="center">
                    No records found
                  </TableCell>
                </TableRow>
              ) : (
                records.map((record) => (
                  <TableRow key={record.id}>
                    <TableCell>{record.pharmacy_name}</TableCell>
                    <TableCell>{record.generated_id}</TableCell>
                    <TableCell>{record.product || '-'}</TableCell>
                    <TableCell align="right">{Number(record.quantity || 0)}</TableCell>
                    <TableCell align="right">{Number(record.amount || 0).toFixed(2)}</TableCell>
                    <TableCell>
                      <Chip
                        label={record.status}
                        color={getStatusColor(record.status)}
                        icon={getStatusIcon(record.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{record.mapped_to || '-'}</TableCell>
                    <TableCell>
                      {new Date(record.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      {record.status === 'pending' && (
                        <>
                          <Tooltip title="Map to Master Pharmacy">
                            <IconButton
                              size="small"
                              onClick={() => {
                                setSelectedRecord(record);
                                setMapDialogOpen(true);
                              }}
                            >
                              <MapIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Ignore Record">
                            <IconButton
                              size="small"
                              onClick={() => handleIgnoreRecord(record.id)}
                            >
                              <CancelIcon />
                            </IconButton>
                          </Tooltip>
                        </>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        {totalPages > 1 && (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={(e, value) => setPage(value)}
              color="primary"
            />
          </Box>
        )}
      </Paper>

      {/* Map Dialog */}
      <Dialog open={mapDialogOpen} onClose={() => setMapDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Map to Master Pharmacy</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Pharmacy: <strong>{selectedRecord?.pharmacy_name}</strong>
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Generated ID: <strong>{selectedRecord?.generated_id}</strong>
            </Typography>
          </Box>
          
          <Autocomplete
            options={masterPharmacies}
            getOptionLabel={(option) => `${option.pharmacy_name} (${option.pharmacy_id})`}
            value={selectedMasterPharmacy}
            onChange={(e, newValue) => setSelectedMasterPharmacy(newValue)}
            renderInput={(params) => (
              <TextField
                {...params}
                label="Select Master Pharmacy"
                placeholder="Search for a pharmacy..."
              />
            )}
            fullWidth
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMapDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={() => {
              if (selectedMasterPharmacy) {
                handleMapRecord(selectedRecord.id, selectedMasterPharmacy.pharmacy_id);
              }
            }}
            variant="contained"
            disabled={!selectedMasterPharmacy}
          >
            Map Record
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default UnmatchedRecords;
