import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Alert,
  LinearProgress,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ButtonGroup,
} from '@mui/material';
import {
  CloudUpload,
  Description,
  CheckCircle,
  Error,
  Delete,
  Refresh,
  Analytics,
  Download,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import {
  uploadInvoice,
  clearError,
} from '../../store/slices/uploadSlice';
import { analyticsAPI } from '../../services/api';

function FileUpload() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { loading, error, progress, currentUpload, uploads } = useSelector(
    (state) => state.upload
  );
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    setAnalysisResult(null);
    
    try {
      const response = await analyticsAPI.analyze();
      setAnalysisResult(response.data);
      
      if (response.data.success) {
        // Navigate to dashboard to show updated analytics
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Analysis failed:', error);
      setAnalysisResult({
        success: false,
        message: 'Analysis failed. Please try again.'
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleExportData = async (format) => {
    try {
      const response = await analyticsAPI.exportMappedData(format);
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `mapped_data.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
      // You could add a toast notification here
    }
  };

  const onDrop = (acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setUploadedFiles([...uploadedFiles, file]);
      
      // Upload invoice file
      dispatch(uploadInvoice(file));
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    multiple: false,
  });

  const removeFile = (index) => {
    const newFiles = uploadedFiles.filter((_, i) => i !== index);
    setUploadedFiles(newFiles);
  };

  const retryUpload = (file) => {
    dispatch(uploadInvoice(file));
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        File Upload
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Upload invoice files for processing.
      </Typography>

      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Upload Invoice Files
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Upload Excel files containing invoice data with columns: Pharmacy_Name, Product, Quantity, Amount
          </Typography>
          
          <Card
            {...getRootProps()}
            sx={{
              p: 4,
              textAlign: 'center',
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.300',
              bgcolor: isDragActive ? 'action.hover' : 'background.paper',
              cursor: 'pointer',
              '&:hover': {
                borderColor: 'primary.main',
                bgcolor: 'action.hover',
              },
            }}
          >
            <input {...getInputProps()} />
            <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive
                ? 'Drop the file here...'
                : 'Drag & drop an Excel file here, or click to select'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Supports .xlsx and .xls files
            </Typography>
          </Card>

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {typeof error === 'string' ? error : JSON.stringify(error)}
            </Alert>
          )}

          {loading && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" gutterBottom>
                Uploading... {progress}%
              </Typography>
              <LinearProgress variant="determinate" value={progress} />
            </Box>
          )}

          {currentUpload && (
            <Alert severity="success" sx={{ mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                File uploaded successfully!
              </Typography>
              <Typography variant="body2" gutterBottom>
                Processed {currentUpload.processed_rows} rows
              </Typography>
              {currentUpload.summary && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="body2">
                    • Valid rows: {currentUpload.summary.valid_rows}
                  </Typography>
                  <Typography variant="body2">
                    • Invalid rows: {currentUpload.summary.invalid_rows}
                  </Typography>
                  <Typography variant="body2">
                    • Unique pharmacies: {currentUpload.summary.unique_pharmacies}
                  </Typography>
                </Box>
              )}
              {currentUpload.unmatched_pharmacies && currentUpload.unmatched_pharmacies.length > 0 && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="body2" color="warning.main">
                    • Unmatched pharmacies: {currentUpload.unmatched_pharmacies.length}
                  </Typography>
                </Box>
              )}
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Export processed invoice data:
                </Typography>
                <ButtonGroup variant="outlined" size="small">
                  <Button
                    startIcon={<Download />}
                    onClick={() => handleExportData('csv')}
                  >
                    Export CSV
                  </Button>
                  <Button
                    startIcon={<Download />}
                    onClick={() => handleExportData('xlsx')}
                  >
                    Export Excel
                  </Button>
                </ButtonGroup>
              </Box>
            </Alert>
          )}
        </CardContent>
      </Card>

      {uploads.length > 0 && (
        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Upload History
            </Typography>
            <List>
              {uploads.map((upload, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <Description />
                  </ListItemIcon>
                  <ListItemText
                    primary={upload.filename || `Upload ${index + 1}`}
                    secondary={`Processed ${upload.processed_rows || 0} rows`}
                  />
                  <Chip
                    icon={<CheckCircle />}
                    label="Completed"
                    color="success"
                    size="small"
                  />
                </ListItem>
              ))}
            </List>
            
            {/* Analyze Button */}
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Button
                variant="contained"
                size="large"
                startIcon={<Analytics />}
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                sx={{ minWidth: 200 }}
              >
                {isAnalyzing ? 'Analyzing...' : 'Analyze Data'}
              </Button>
              
              {analysisResult && (
                <Alert 
                  severity={analysisResult.success ? 'success' : 'error'} 
                  sx={{ mt: 2 }}
                >
                  {analysisResult.message}
                  {analysisResult.summary && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2">
                        • Total Revenue: ₹{analysisResult.summary.total_revenue?.toLocaleString('en-IN') || 0}
                      </Typography>
                      <Typography variant="body2">
                        • Total Pharmacies: {analysisResult.summary.total_pharmacies || 0}
                      </Typography>
                      <Typography variant="body2">
                        • Total Doctors: {analysisResult.summary.total_doctors || 0}
                      </Typography>
                      <Typography variant="body2">
                        • Matched Records: {analysisResult.summary.matched_records || 0}
                      </Typography>
                    </Box>
                  )}
                  {analysisResult.success && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2" gutterBottom>
                        Download mapped data:
                      </Typography>
                      <ButtonGroup variant="outlined" size="small">
                        <Button
                          startIcon={<Download />}
                          onClick={() => handleExportData('csv')}
                        >
                          Export CSV
                        </Button>
                        <Button
                          startIcon={<Download />}
                          onClick={() => handleExportData('xlsx')}
                        >
                          Export Excel
                        </Button>
                      </ButtonGroup>
                    </Box>
                  )}
                </Alert>
              )}
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

export default FileUpload;
