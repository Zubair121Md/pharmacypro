import React, { useState, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Alert,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  TextField,
  InputAdornment,
  Chip,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
} from '@mui/material';
import {
  Refresh,
  CallSplit,
  Delete as DeleteIcon,
  CloudUpload,
  Download,
} from '@mui/icons-material';
import { masterDataAPI, splitRuleAPI, analyticsAPI } from '../../services/api';

function SplitRatioManagement() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [duplicates, setDuplicates] = useState([]);
  const [splitDialogOpen, setSplitDialogOpen] = useState(false);
  const [selectedDuplicate, setSelectedDuplicate] = useState(null);
  const [splitRatios, setSplitRatios] = useState([]);
  const [existingRules, setExistingRules] = useState([]);
  const [uploading, setUploading] = useState(false);

  // Fetch duplicates
  const fetchDuplicates = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await masterDataAPI.getDuplicates();
      setDuplicates(response.data.duplicates || []);
    } catch (err) {
      console.error('Error fetching duplicates:', err);
      setError('Failed to fetch duplicate combinations');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch existing split rules
  const fetchSplitRules = useCallback(async () => {
    try {
      const response = await splitRuleAPI.getSplitRules();
      setExistingRules(response.data || []);
    } catch (err) {
      console.error('Error fetching split rules:', err);
    }
  }, []);

  useEffect(() => {
    fetchDuplicates();
    fetchSplitRules();
  }, [fetchDuplicates, fetchSplitRules]);

  // Check if a duplicate has an existing rule
  const hasExistingRule = (duplicate) => {
    const productKey = `${duplicate.pharmacy_id}|EXACT|${duplicate.normalized_product}`;
    return existingRules.some(rule => 
      rule.pharmacy_id === duplicate.pharmacy_id && 
      rule.product_key === productKey
    );
  };

  // Get existing rule for a duplicate
  const getExistingRule = (duplicate) => {
    const productKey = `${duplicate.pharmacy_id}|EXACT|${duplicate.normalized_product}`;
    return existingRules.find(rule => 
      rule.pharmacy_id === duplicate.pharmacy_id && 
      rule.product_key === productKey
    );
  };

  // Handle opening split dialog
  const handleOpenSplitDialog = (duplicate) => {
    setSelectedDuplicate(duplicate);
    setError(null);
    
    const existingRule = getExistingRule(duplicate);
    
    if (existingRule && existingRule.rules) {
      // Load existing ratios
      setSplitRatios(duplicate.records.map(record => {
        const ruleEntry = existingRule.rules.find(r => r.master_mapping_id === record.id);
        return {
          master_mapping_id: record.id,
          doctor_name: record.doctor_name,
          doctor_id: record.doctor_id,
          ratio: ruleEntry ? ruleEntry.ratio : 0
        };
      }));
    } else {
      // Initialize ratios with equal split
      const equalRatio = 100 / duplicate.records.length;
      setSplitRatios(duplicate.records.map(record => ({
        master_mapping_id: record.id,
        doctor_name: record.doctor_name,
        doctor_id: record.doctor_id,
        ratio: Math.round(equalRatio * 10) / 10
      })));
    }
    
    setSplitDialogOpen(true);
  };

  const handleCloseSplitDialog = () => {
    setSplitDialogOpen(false);
    setSelectedDuplicate(null);
    setSplitRatios([]);
    setError(null);
  };

  const handleSplitRatioChange = (index, value) => {
    const newRatios = [...splitRatios];
    newRatios[index].ratio = parseFloat(value) || 0;
    setSplitRatios(newRatios);
  };

  const handleSaveSplitRule = async () => {
    try {
      setError(null);
      
      // Validate ratios sum to 100
      const totalRatio = splitRatios.reduce((sum, r) => sum + r.ratio, 0);
      if (Math.abs(totalRatio - 100) > 0.1) {
        setError(`Ratios must sum to 100% (current: ${totalRatio.toFixed(1)}%)`);
        return;
      }

      const productKey = `${selectedDuplicate.pharmacy_id}|EXACT|${selectedDuplicate.normalized_product}`;
      
      const response = await splitRuleAPI.createSplitRule({
        pharmacy_id: selectedDuplicate.pharmacy_id,
        product_key: productKey,
        rules: splitRatios.map(r => ({
          master_mapping_id: r.master_mapping_id,
          ratio: r.ratio
        }))
      });

      const invoicesReprocessed = response.data.invoices_reprocessed || 0;
      const successMsg = invoicesReprocessed > 0
        ? `✅ Split rule saved! ${invoicesReprocessed} existing invoice(s) reprocessed. Refreshing analytics...`
        : '✅ Split rule saved! Will apply to future invoices.';
      
      setSuccess(successMsg);
      handleCloseSplitDialog();
      fetchDuplicates();
      fetchSplitRules();
      
      // Clear analytics cache and trigger refresh if invoices were reprocessed
      if (invoicesReprocessed > 0) {
        try {
          await analyticsAPI.clearCache();
          // Dispatch custom event to notify Dashboard/Analytics to refresh
          window.dispatchEvent(new CustomEvent('analyticsDataUpdated'));
          setTimeout(() => {
            setSuccess(`✅ Split rule saved! ${invoicesReprocessed} invoice(s) reprocessed. Analytics updated - Dashboard should refresh automatically.`);
          }, 1000);
        } catch (cacheErr) {
          console.warn('Could not clear analytics cache:', cacheErr);
          setTimeout(() => {
            setSuccess(`✅ Split rule saved! ${invoicesReprocessed} invoice(s) reprocessed. Please manually refresh the Dashboard/Analytics page.`);
          }, 1000);
        }
      }
      
      setTimeout(() => setSuccess(null), 8000);
    } catch (err) {
      console.error('Error saving split rule:', err);
      setError(err.response?.data?.detail || 'Failed to save split rule');
    }
  };

  const handleDeleteRule = async (duplicate) => {
    const existingRule = getExistingRule(duplicate);
    if (!existingRule) return;

    if (!window.confirm('Delete this split rule? Future invoices will use the default (first doctor).')) {
      return;
    }

    try {
      await splitRuleAPI.deleteSplitRule(existingRule.id);
      setSuccess('Split rule deleted successfully');
      setTimeout(() => setSuccess(null), 3000);
      fetchSplitRules();
    } catch (err) {
      console.error('Error deleting split rule:', err);
      setError('Failed to delete split rule');
    }
  };

  const handleRefresh = () => {
    fetchDuplicates();
    fetchSplitRules();
  };

  const handleExportExcel = async () => {
    try {
      setError(null);
      const res = await splitRuleAPI.exportExcel();
      const url = window.URL.createObjectURL(
        new Blob([res.data], { 
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
        })
      );
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `split_rules_backup_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setSuccess('Split rules exported successfully!');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to export split rules');
      console.error('Error exporting split rules:', err);
    }
  };

  const onDrop = async (acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setUploading(true);
      setError(null);
      setSuccess(null);

      try {
        const response = await splitRuleAPI.importExcel(file);
        
        const message = response.data.message || 
          `Import completed: ${response.data.imported || 0} new rules, ${response.data.updated || 0} updated rules`;
        setSuccess(message);
        
        if (response.data.errors && response.data.errors.length > 0) {
          console.warn('Import errors:', response.data.errors);
          setError(`Import completed with ${response.data.errors.length} errors. Check console for details.`);
        }
        
        // Refresh the data
        setTimeout(() => {
          fetchDuplicates();
          fetchSplitRules();
          // Clear analytics cache and trigger refresh
          analyticsAPI.clearCache().then(() => {
            window.dispatchEvent(new CustomEvent('analyticsDataUpdated'));
          }).catch(err => console.warn('Could not clear analytics cache:', err));
        }, 1000);
        
        setTimeout(() => {
          setSuccess(null);
          setError(null);
        }, 8000);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to import split rules');
        console.error('Error importing split rules:', err);
      } finally {
        setUploading(false);
      }
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    multiple: false,
    disabled: uploading,
  });

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Revenue Split Ratio Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage revenue distribution for pharmacy + product combinations with multiple doctors.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<CloudUpload />}
            onClick={() => document.querySelector('#split-rules-file-input')?.click()}
            disabled={uploading || loading}
          >
            {uploading ? 'Uploading...' : 'Import Excel'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={handleExportExcel}
            disabled={loading}
          >
            Export Excel
          </Button>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

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

      {/* Excel Upload Area */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box {...getRootProps()} sx={{ 
            border: '2px dashed', 
            borderColor: isDragActive ? 'primary.main' : 'grey.300',
            borderRadius: 2,
            p: 3,
            textAlign: 'center',
            cursor: uploading ? 'not-allowed' : 'pointer',
            bgcolor: isDragActive ? 'action.hover' : 'background.paper',
            transition: 'all 0.2s',
            '&:hover': {
              borderColor: 'primary.main',
              bgcolor: 'action.hover'
            }
          }}>
            <input {...getInputProps()} id="split-rules-file-input" />
            <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive ? 'Drop Excel file here' : 'Upload Split Rules Excel File'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Drag and drop an Excel file here, or click to select
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Required columns: Pharmacy_ID, Product_Key, Master_Mapping_ID, Ratio_Percentage
            </Typography>
            {uploading && (
              <Box sx={{ mt: 2 }}>
                <CircularProgress size={24} />
              </Box>
            )}
          </Box>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <CallSplit sx={{ mr: 1, color: 'warning.main' }} />
            <Typography variant="h6">
              Duplicate Pharmacy + Product Combinations
            </Typography>
            <Chip 
              label={`${duplicates.length} duplicates`} 
              color={duplicates.length > 0 ? 'warning' : 'success'}
              size="small" 
              sx={{ ml: 2 }} 
            />
          </Box>

          <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
            When multiple doctors are assigned to the same pharmacy + product, you can set custom split ratios 
            to distribute revenue during invoice uploads. Changes apply immediately to existing invoices.
          </Typography>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : duplicates.length === 0 ? (
            <Alert severity="info">
              No duplicate combinations found. All pharmacy + product pairs have unique doctor assignments.
            </Alert>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow sx={{ bgcolor: 'action.hover' }}>
                    <TableCell sx={{ fontWeight: 'bold' }}>Pharmacy</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Product</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Doctors ({'>'}1)</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }} align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {duplicates.map((dup, idx) => {
                    const hasRule = hasExistingRule(dup);
                    const rule = getExistingRule(dup);
                    
                    return (
                      <TableRow key={idx} hover>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                            {dup.pharmacy_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {dup.pharmacy_id}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{dup.product_name}</Typography>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {dup.records.map((rec, i) => {
                              const ruleEntry = rule?.rules?.find(r => r.master_mapping_id === rec.id);
                              return (
                                <Chip 
                                  key={i}
                                  label={`${rec.doctor_name}${ruleEntry ? ` (${ruleEntry.ratio}%)` : ''}`}
                                  size="small"
                                  color={ruleEntry ? 'primary' : 'default'}
                                />
                              );
                            })}
                          </Box>
                        </TableCell>
                        <TableCell>
                          {hasRule ? (
                            <Chip label="Rule Set" color="success" size="small" />
                          ) : (
                            <Chip label="No Rule" color="warning" size="small" />
                          )}
                        </TableCell>
                        <TableCell align="right">
                          <Button
                            size="small"
                            variant={hasRule ? 'outlined' : 'contained'}
                            color="primary"
                            onClick={() => handleOpenSplitDialog(dup)}
                            sx={{ mr: 1 }}
                          >
                            {hasRule ? 'Edit Ratio' : 'Set Ratio'}
                          </Button>
                          {hasRule && (
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleDeleteRule(dup)}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Split Ratio Dialog */}
      <Dialog open={splitDialogOpen} onClose={handleCloseSplitDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <CallSplit sx={{ mr: 1 }} />
            Set Revenue Split Ratio
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedDuplicate && (
            <Box sx={{ mt: 2 }}>
              <Paper sx={{ p: 2, mb: 3, bgcolor: 'primary.50' }}>
                <Typography variant="body1" gutterBottom>
                  <strong>Pharmacy:</strong> {selectedDuplicate.pharmacy_name}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  ID: {selectedDuplicate.pharmacy_id}
                </Typography>
                <Typography variant="body1" gutterBottom sx={{ mt: 1 }}>
                  <strong>Product:</strong> {selectedDuplicate.product_name}
                </Typography>
              </Paper>

              <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mb: 2 }}>
                Distribute revenue percentage across doctors (must sum to 100%):
              </Typography>

              {splitRatios.map((ratioEntry, index) => (
                <Grid container spacing={2} key={index} sx={{ mb: 2, alignItems: 'center' }}>
                  <Grid item xs={7}>
                    <Paper sx={{ p: 1.5, bgcolor: 'action.hover' }}>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        {ratioEntry.doctor_name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        ID: {ratioEntry.doctor_id}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={5}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Ratio (%)"
                      value={ratioEntry.ratio}
                      onChange={(e) => handleSplitRatioChange(index, e.target.value)}
                      inputProps={{ step: '0.1', min: '0', max: '100' }}
                      InputProps={{
                        endAdornment: <InputAdornment position="end">%</InputAdornment>
                      }}
                      size="small"
                    />
                  </Grid>
                </Grid>
              ))}

              <Paper sx={{ mt: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                    Total:
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {splitRatios.reduce((sum, r) => sum + r.ratio, 0).toFixed(1)}%
                    </Typography>
                    {Math.abs(splitRatios.reduce((sum, r) => sum + r.ratio, 0) - 100) > 0.1 ? (
                      <Chip label="Must equal 100%" color="error" size="small" />
                    ) : (
                      <Chip label="Valid" color="success" size="small" />
                    )}
                  </Box>
                </Box>
              </Paper>

              {error && (
                <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
                  {error}
                </Alert>
              )}

              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Note:</strong> Saving this rule will immediately reprocess all existing invoices 
                  for this pharmacy + product combination and update analytics in real-time.
                </Typography>
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={handleCloseSplitDialog}>
            Cancel
          </Button>
          <Button 
            onClick={handleSaveSplitRule} 
            variant="contained" 
            color="primary"
            disabled={Math.abs(splitRatios.reduce((sum, r) => sum + r.ratio, 0) - 100) > 0.1}
          >
            Save Split Rule
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default SplitRatioManagement;

