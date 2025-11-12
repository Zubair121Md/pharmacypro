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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Refresh,
  Map,
  Block,
  Search,
  FilterList,
} from '@mui/icons-material';
import { unmatchedAPI } from '../../services/api';

function UnmatchedRecords() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [mappingData, setMappingData] = useState({
    pharmacy_id: '',
    notes: '',
  });
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [masterPharmacies, setMasterPharmacies] = useState([]);

  useEffect(() => {
    fetchUnmatchedRecords();
  }, []);

  const fetchUnmatchedRecords = async () => {
    try {
      setLoading(true);
      const response = await unmatchedAPI.getUnmatchedRecords();
      setRecords(response.data);
    } catch (error) {
      setError('Failed to fetch unmatched records');
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
      const response = await unmatchedAPI.getMasterPharmacies();
      setMasterPharmacies(response.data);
    } catch (error) {
      console.error('Failed to fetch master pharmacies:', error);
    }
  };

  const handleMapRecord = (record) => {
    setSelectedRecord(record);
    setMappingData({
      pharmacy_id: '',
      notes: '',
    });
    fetchMasterPharmacies();
    setOpenDialog(true);
  };

  const handleIgnoreRecord = async (recordId) => {
    if (window.confirm('Are you sure you want to ignore this record?')) {
      try {
        await unmatchedAPI.ignoreRecord(recordId);
        fetchUnmatchedRecords();
      } catch (error) {
        setError('Failed to ignore record');
      }
    }
  };

  const handleMappingSubmit = async () => {
    try {
      await unmatchedAPI.mapRecord(selectedRecord.id, mappingData);
      setOpenDialog(false);
      fetchUnmatchedRecords();
    } catch (error) {
      setError('Failed to map record');
    }
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedRecord(null);
    setMappingData({
      pharmacy_id: '',
      notes: '',
    });
  };

  const filteredRecords = records.filter(record => {
    const matchesFilter = filter === 'all' || record.status === filter;
    const matchesSearch = record.pharmacy_name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'warning';
      case 'mapped':
        return 'success';
      case 'ignored':
        return 'error';
      default:
        return 'default';
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
          Unmatched Records
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={fetchUnmatchedRecords}
        >
          Refresh
        </Button>
      </Box>

      <Typography variant="body1" color="text.secondary" gutterBottom>
        Review and manage pharmacy records that couldn't be automatically matched.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Box display="flex" gap={2} mb={2} alignItems="center">
            <TextField
              size="small"
              placeholder="Search pharmacy names..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Filter</InputLabel>
              <Select
                value={filter}
                label="Filter"
                onChange={(e) => setFilter(e.target.value)}
              >
                <MenuItem value="all">All Records</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="mapped">Mapped</MenuItem>
                <MenuItem value="ignored">Ignored</MenuItem>
              </Select>
            </FormControl>
          </Box>

          <TableContainer component={Paper}>
            <Box sx={{ p: 2, display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
              <Button variant="outlined" onClick={handleExportCSV}>Export CSV</Button>
              <Button variant="outlined" onClick={handleExportExcel}>Export Excel</Button>
            </Box>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Pharmacy Name</TableCell>
                  <TableCell>Generated ID</TableCell>
                  <TableCell>Product</TableCell>
                  <TableCell align="right">Quantity</TableCell>
                  <TableCell align="right">Revenue</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredRecords.map((record) => (
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
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {new Date(record.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Tooltip title="Map to existing pharmacy">
                        <IconButton
                          size="small"
                          onClick={() => handleMapRecord(record)}
                          disabled={record.status === 'mapped'}
                        >
                          <Map />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Ignore record">
                        <IconButton
                          size="small"
                          onClick={() => handleIgnoreRecord(record.id)}
                          disabled={record.status === 'ignored'}
                          color="error"
                        >
                          <Block />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {filteredRecords.length === 0 && (
            <Box textAlign="center" py={4}>
              <Typography variant="body1" color="text.secondary">
                No unmatched records found
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Mapping Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          Map Pharmacy Record
        </DialogTitle>
        <DialogContent>
          {selectedRecord && (
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Mapping: <strong>{selectedRecord.pharmacy_name}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Generated ID: <strong>{selectedRecord.generated_id}</strong>
              </Typography>
              
              <FormControl fullWidth sx={{ mt: 2 }}>
                <InputLabel>Select Master Pharmacy</InputLabel>
                <Select
                  value={mappingData.pharmacy_id}
                  label="Select Master Pharmacy"
                  onChange={(e) => setMappingData({
                    ...mappingData,
                    pharmacy_id: e.target.value,
                  })}
                >
                  {masterPharmacies.map((pharmacy) => (
                    <MenuItem key={pharmacy.pharmacy_id} value={pharmacy.pharmacy_id}>
                      {pharmacy.pharmacy_name} ({pharmacy.pharmacy_id})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <TextField
                fullWidth
                label="Notes"
                name="notes"
                multiline
                rows={3}
                value={mappingData.notes}
                onChange={(e) => setMappingData({
                  ...mappingData,
                  notes: e.target.value,
                })}
                sx={{ mt: 2 }}
                placeholder="Add any notes about this mapping"
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleMappingSubmit} variant="contained">
            Map Record
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default UnmatchedRecords;

