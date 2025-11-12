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
} from '@mui/material';
import {
  Inventory as ProductIcon,
  ContentCopy as CopyIcon,
  Add as AddIcon,
} from '@mui/icons-material';

const ProductGenerator = () => {
  const [productInput, setProductInput] = useState('');
  const [generatedIds, setGeneratedIds] = useState([]);
  const [error, setError] = useState('');

  const normalizeText = (text) => {
    if (!text) return '';
    return text
      .toUpperCase()
      .replace(/[^A-Z0-9]/g, '')
      .substring(0, 8)
      .padEnd(8, '-');
  };

  const generateId = (text) => {
    const normalized = normalizeText(text);
    return `PX-${normalized}`;
  };

  const handleGenerate = () => {
    if (!productInput.trim()) {
      setError('Please enter a product name to generate ID');
      return;
    }

    const generatedId = generateId(productInput);
    const newEntry = {
      id: Date.now(),
      originalName: productInput,
      generatedId,
      timestamp: new Date().toLocaleString(),
    };

    setGeneratedIds(prev => [newEntry, ...prev]);
    setError('');
    setProductInput('');
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
        <ProductIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Product ID Generator
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Generate standardized product IDs with PX- prefix
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Generate New Product ID
              </Typography>
              <TextField
                fullWidth
                label="Product Name"
                value={productInput}
                onChange={(e) => setProductInput(e.target.value)}
                placeholder="e.g., BRETHNOL SYP"
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
                startIcon={<AddIcon />}
                disabled={!productInput.trim()}
              >
                Generate Product ID
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
              {productInput ? (
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Input: {productInput}
                  </Typography>
                  <Typography variant="h6" sx={{ mt: 1, fontFamily: 'monospace' }}>
                    Generated: {generateId(productInput)}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Enter a product name to see the generated ID
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
              Generated Product IDs
            </Typography>
            <Button variant="outlined" onClick={clearHistory}>
              Clear History
            </Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Product Name</TableCell>
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
                        <ProductIcon sx={{ mr: 1, color: 'primary.main' }} />
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

export default ProductGenerator;


