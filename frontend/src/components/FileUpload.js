import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Container,
  Typography,
  Paper,
  Box,
  Button,
  Alert,
  LinearProgress,
  Grid,
  Card,
  CardContent,
  Chip,
  Divider,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Description as FileIcon,
} from '@mui/icons-material';
import axios from 'axios';

const FileUpload = () => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState(null);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://localhost:8000';

  const onDrop = useCallback(async (acceptedFiles) => {
    setError(null);
    setUploadResult(null);
    
    if (acceptedFiles.length === 0) return;
    
    const formData = new FormData();
    
    // Determine file types and add to form data
    const masterFile = acceptedFiles.find(file => 
      file.name.toLowerCase().includes('master') || 
      file.name.toLowerCase().includes('mapping')
    );
    const invoiceFile = acceptedFiles.find(file => 
      file.name.toLowerCase().includes('invoice') || 
      file.name.toLowerCase().includes('sales')
    );
    
    if (masterFile && invoiceFile) {
      formData.append('master', masterFile);
      formData.append('invoice', invoiceFile);
    } else if (masterFile) {
      formData.append('master', masterFile);
    } else if (invoiceFile) {
      formData.append('invoice', invoiceFile);
    } else {
      setError('Please upload files with "master" or "invoice" in the filename');
      return;
    }
    
    try {
      setUploading(true);
      setUploadProgress(0);
      
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);
      
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/upload/enhanced`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadResult(response.data);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    multiple: true,
    disabled: uploading
  });

  const resetUpload = () => {
    setUploadResult(null);
    setError(null);
    setUploadProgress(0);
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          File Upload
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Upload master data and invoice files for processing and ID generation
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Upload Area */}
        <Grid item xs={12} md={8}>
          <Paper
            {...getRootProps()}
            sx={{
              p: 4,
              textAlign: 'center',
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.300',
              backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
              cursor: uploading ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
              '&:hover': {
                borderColor: 'primary.main',
                backgroundColor: 'action.hover'
              }
            }}
          >
            <input {...getInputProps()} />
            
            <UploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            
            {isDragActive ? (
              <Typography variant="h6" color="primary">
                Drop the files here...
              </Typography>
            ) : (
              <>
                <Typography variant="h6" gutterBottom>
                  Drag & drop files here, or click to select
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Supports Excel files (.xlsx, .xls)
                </Typography>
                <Button variant="contained" disabled={uploading}>
                  Choose Files
                </Button>
              </>
            )}
            
            {uploading && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress variant="determinate" value={uploadProgress} />
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Uploading... {uploadProgress}%
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Instructions */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Upload Instructions
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>Master Data File:</strong> Should contain pharmacy mapping data with columns:
              </Typography>
              <Box sx={{ ml: 2, mb: 2 }}>
                <Chip label="REP_Names" size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                <Chip label="Doctor_Names" size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                <Chip label="Pharmacy_Names" size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                <Chip label="Product_Names" size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                <Chip label="Product_Price" size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                <Chip label="HQ" size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                <Chip label="AREA" size="small" sx={{ mr: 0.5, mb: 0.5 }} />
              </Box>
              
              <Typography variant="body2" paragraph>
                <strong>Invoice Data File:</strong> Should contain sales data with columns:
              </Typography>
              <Box sx={{ ml: 2, mb: 2 }}>
                <Chip label="Pharmacy_Name" size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                <Chip label="Product" size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                <Chip label="Quantity" size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                <Chip label="Amount" size="small" sx={{ mr: 0.5, mb: 0.5 }} />
              </Box>
              
              <Typography variant="body2" color="text.secondary">
                The system will automatically generate unique IDs for pharmacy names and match them with master data.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Results */}
        {uploadResult && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <CheckIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="h6" color="success.main">
                  Upload Successful
                </Typography>
              </Box>
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="primary">
                      {uploadResult.rows_processed}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Rows Processed
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="success.main">
                      {uploadResult.matched_count}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Matched Records
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="warning.main">
                      {uploadResult.unmatched_count}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Unmatched Records
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="info.main">
                      {uploadResult.file_id}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      File ID
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="body2" color="text.secondary" paragraph>
                {uploadResult.message}
              </Typography>
              
              <Button variant="outlined" onClick={resetUpload}>
                Upload Another File
              </Button>
            </Paper>
          </Grid>
        )}

        {/* Error */}
        {error && (
          <Grid item xs={12}>
            <Alert 
              severity="error" 
              icon={<ErrorIcon />}
              action={
                <Button color="inherit" size="small" onClick={resetUpload}>
                  Try Again
                </Button>
              }
            >
              {typeof error === 'string' ? error : JSON.stringify(error)}
            </Alert>
          </Grid>
        )}
      </Grid>
    </Container>
  );
};

export default FileUpload;
