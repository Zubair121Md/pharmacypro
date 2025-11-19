import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
  CircularProgress,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Pagination,
} from '@mui/material';
import {
  Inventory as ProductIcon,
  ContentCopy as CopyIcon,
  Add as AddIcon,
  CloudUpload as UploadIcon,
  Refresh,
  Search,
  Clear,
  Edit,
  Save,
  Cancel,
  Delete,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { generatorAPI, productDataAPI } from '../../services/api';
import { debounce } from 'lodash';

const ProductGenerator = () => {
  const [productInput, setProductInput] = useState('');
  const [generatedIds, setGeneratedIds] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  
  // Product data management states
  const [allProducts, setAllProducts] = useState([]);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [limit] = useState(50);
  const [editingId, setEditingId] = useState(null);
  const [editData, setEditData] = useState({});
  const [saving, setSaving] = useState(false);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [newProduct, setNewProduct] = useState({
    product_name: '',
    product_id: '',
    product_price: '',
  });

  // Fetch all products
  const fetchAllProducts = useCallback(async () => {
    setLoadingProducts(true);
    setError('');
    try {
      const response = await productDataAPI.getAllProducts();
      setAllProducts(response.data || []);
    } catch (err) {
      setError('Failed to fetch products');
      console.error('Error fetching products:', err);
    } finally {
      setLoadingProducts(false);
    }
  }, []);

  useEffect(() => {
    fetchAllProducts();
  }, [fetchAllProducts]);

  // Auto-generate ID when product name changes
  useEffect(() => {
    if (newProduct.product_name && addDialogOpen) {
      // Generate ID based on product name (simple sequential for now)
      // In a real scenario, you might want to call the generator API
      const autoId = allProducts.length > 0 
        ? Math.max(...allProducts.map(p => p.product_id || 0)) + 1
        : 1;
      setNewProduct(prev => ({ ...prev, product_id: autoId.toString() }));
    }
  }, [newProduct.product_name, addDialogOpen, allProducts]);

  const handleGenerate = async () => {
    if (!productInput.trim()) {
      setError('Please enter a product name to generate ID');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await generatorAPI.generateId(productInput.trim(), 'product');
      const newEntry = {
        id: Date.now(),
        originalName: productInput,
        generatedId: response.data.generated_id,
        price: response.data.metadata?.price,
        matchedOriginal: response.data.metadata?.matched_original,
        timestamp: new Date().toLocaleString(),
      };

      setGeneratedIds(prev => [newEntry, ...prev]);
      setProductInput('');
      
      // Refresh product list
      fetchAllProducts();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate product ID. Make sure product reference table is uploaded.');
    } finally {
      setLoading(false);
    }
  };

  const onDrop = async (acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setUploading(true);
      setError('');
      setSuccess('');
      
      try {
        const response = await generatorAPI.uploadProductReference(file);
        setSuccess(`Product reference table uploaded! ${response.data.records_added} records added, ${response.data.records_updated} updated.`);
        setTimeout(() => setSuccess(''), 5000);
        // Refresh product list
        fetchAllProducts();
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to upload product reference table');
      } finally {
        setUploading(false);
      }
    }
  };

  // Search functionality
  const searchInData = useCallback((data, query) => {
    if (!query.trim()) return data;
    const lowerQuery = query.toLowerCase().trim();
    return data.filter((row) => {
      const searchableText = [
        row.product_name || '',
        row.product_id?.toString() || '',
        row.product_price?.toString() || '',
      ].join(' ').toLowerCase();
      return searchableText.includes(lowerQuery);
    });
  }, []);

  const debouncedSearch = useMemo(
    () => debounce((query) => setSearchQuery(query), 300),
    []
  );

  const handleSearchChange = (event) => {
    debouncedSearch(event.target.value);
    setPage(1);
  };

  const clearSearch = () => {
    setSearchQuery('');
    setPage(1);
  };

  const filteredProducts = useMemo(
    () => searchInData(allProducts, searchQuery),
    [allProducts, searchQuery, searchInData]
  );

  const paginatedProducts = useMemo(() => {
    const startIndex = (page - 1) * limit;
    return filteredProducts.slice(startIndex, startIndex + limit);
  }, [filteredProducts, page, limit]);

  // Add new product
  const handleAddNew = () => {
    setNewProduct({
      product_name: '',
      product_id: '',
      product_price: '',
    });
    setError('');
    setAddDialogOpen(true);
  };

  const handleCloseAddDialog = () => {
    setAddDialogOpen(false);
    setNewProduct({
      product_name: '',
      product_id: '',
      product_price: '',
    });
    setError('');
  };

  const handleSaveNew = async () => {
    if (!newProduct.product_name) {
      setError('Product name is required');
      return;
    }

    setSaving(true);
    setError('');
    try {
      const productData = {
        product_name: newProduct.product_name,
        product_id: newProduct.product_id ? parseInt(newProduct.product_id) : undefined,
        product_price: newProduct.product_price ? parseFloat(newProduct.product_price) : 0.0,
      };

      await productDataAPI.createProduct(productData);
      setSuccess('Product created successfully!');
      setAddDialogOpen(false);
      fetchAllProducts();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create product');
      console.error('Error creating product:', err);
    } finally {
      setSaving(false);
    }
  };

  // Edit product
  const handleEdit = (product) => {
    setEditingId(product.id);
    setEditData({
      product_name: product.product_name,
      product_id: product.product_id,
      product_price: product.product_price,
    });
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditData({});
    setError(null);
  };

  const handleSaveEdit = async () => {
    setSaving(true);
    setError(null);
    try {
      await productDataAPI.updateProduct(editingId, editData);
      setSuccess('Product updated successfully!');
      setEditingId(null);
      setEditData({});
      fetchAllProducts();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update product');
      console.error('Error updating product:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleFieldChange = (field, value) => {
    setEditData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  // Delete product
  const handleDelete = async (productId) => {
    if (!window.confirm('Are you sure you want to delete this product?')) {
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await productDataAPI.deleteProduct(productId);
      setSuccess('Product deleted successfully!');
      fetchAllProducts();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete product');
      console.error('Error deleting product:', err);
    } finally {
      setSaving(false);
    }
  };

  const EditableCell = ({ value, field, editing, onChange, type = 'text' }) => {
    if (editing) {
      return (
        <TextField
          size="small"
          type={type}
          value={value || ''}
          onChange={(e) => onChange(field, type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value)}
          variant="outlined"
          fullWidth
          sx={{
            '& .MuiOutlinedInput-root': {
              fontSize: '0.875rem',
            },
          }}
        />
      );
    }
    return value || '-';
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
        Generate product IDs by matching against reference table. Upload product reference table first.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {/* Upload Product Reference Table */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Upload Product Reference Table
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Upload Excel file with columns: Product Name, mprice
          </Typography>
          <Paper
            {...getRootProps()}
            sx={{
              p: 3,
              textAlign: 'center',
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.300',
              bgcolor: isDragActive ? 'action.hover' : 'background.paper',
              cursor: uploading ? 'not-allowed' : 'pointer',
              opacity: uploading ? 0.6 : 1,
            }}
          >
            <input {...getInputProps()} />
            {uploading ? (
              <CircularProgress sx={{ mb: 2 }} />
            ) : (
              <UploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            )}
            <Typography variant="body1" gutterBottom>
              {uploading
                ? 'Uploading...'
                : isDragActive
                ? 'Drop the file here...'
                : 'Drag & drop Excel file here, or click to select'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Supports .xlsx and .xls files
            </Typography>
          </Paper>
        </CardContent>
      </Card>

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
                startIcon={loading ? <CircularProgress size={20} /> : <AddIcon />}
                disabled={!productInput.trim() || loading}
              >
                {loading ? 'Generating...' : 'Generate Product ID'}
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
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Click "Generate Product ID" to match against reference table
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Enter a product name to generate ID
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
                  <TableCell>Matched Original</TableCell>
                  <TableCell>Price</TableCell>
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
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {entry.matchedOriginal || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {entry.price ? `₹${entry.price.toFixed(2)}` : '-'}
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

      {/* Product Data Management Section */}
      <Card sx={{ mt: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">
              Product Data Management
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                startIcon={<Refresh />}
                onClick={fetchAllProducts}
                disabled={loadingProducts}
                variant="outlined"
              >
                {loadingProducts ? 'Refreshing...' : 'Refresh'}
              </Button>
              <Button
                startIcon={<AddIcon />}
                onClick={handleAddNew}
                variant="contained"
              >
                Add New Product
              </Button>
            </Box>
          </Box>

          <TextField
            fullWidth
            variant="outlined"
            placeholder="Search products by name, ID, or price..."
            value={searchQuery}
            onChange={handleSearchChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search color="action" />
                </InputAdornment>
              ),
              endAdornment: searchQuery && (
                <InputAdornment position="end">
                  <IconButton
                    aria-label="clear search"
                    onClick={clearSearch}
                    edge="end"
                    size="small"
                  >
                    <Clear />
                  </IconButton>
                </InputAdornment>
              ),
            }}
            sx={{ mb: 2 }}
          />

          {searchQuery && (
            <Box sx={{ mb: 2 }}>
              <Chip
                label={`Found ${filteredProducts.length} result${filteredProducts.length !== 1 ? 's' : ''} for "${searchQuery}"`}
                color="primary"
                variant="outlined"
                onDelete={clearSearch}
              />
            </Box>
          )}

          {loadingProducts ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : allProducts.length === 0 ? (
            <Alert severity="info">
              No products found. Add a new product or upload a product reference table.
            </Alert>
          ) : filteredProducts.length === 0 ? (
            <Alert severity="warning">
              No results found for "{searchQuery}". Try a different search term.
            </Alert>
          ) : (
            <>
              <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: '70vh' }}>
                <Table stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Product Name</strong></TableCell>
                      <TableCell><strong>Product ID</strong></TableCell>
                      <TableCell><strong>Price</strong></TableCell>
                      <TableCell><strong>Actions</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {paginatedProducts.map((row) => {
                      const isEditing = editingId === row.id;
                      return (
                        <TableRow key={row.id} hover sx={{ bgcolor: isEditing ? 'action.hover' : 'inherit' }}>
                          <TableCell>
                            {isEditing ? (
                              <EditableCell
                                value={editData.product_name}
                                field="product_name"
                                editing={isEditing}
                                onChange={handleFieldChange}
                              />
                            ) : (
                              row.product_name || '-'
                            )}
                          </TableCell>
                          <TableCell>
                            {isEditing ? (
                              <EditableCell
                                value={editData.product_id}
                                field="product_id"
                                editing={isEditing}
                                onChange={handleFieldChange}
                                type="number"
                              />
                            ) : (
                              <Typography variant="body2" fontFamily="monospace">
                                {row.product_id || '-'}
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            {isEditing ? (
                              <EditableCell
                                value={editData.product_price}
                                field="product_price"
                                editing={isEditing}
                                onChange={handleFieldChange}
                                type="number"
                              />
                            ) : (
                              row.product_price ? `₹${parseFloat(row.product_price).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-'
                            )}
                          </TableCell>
                          <TableCell>
                            {isEditing ? (
                              <Box sx={{ display: 'flex', gap: 0.5 }}>
                                <IconButton size="small" color="primary" onClick={handleSaveEdit} disabled={saving} title="Save">
                                  {saving ? <CircularProgress size={20} /> : <Save />}
                                </IconButton>
                                <IconButton size="small" color="error" onClick={handleCancelEdit} disabled={saving} title="Cancel">
                                  <Cancel />
                                </IconButton>
                              </Box>
                            ) : (
                              <Box sx={{ display: 'flex', gap: 0.5 }}>
                                <IconButton size="small" color="warning" onClick={() => handleEdit(row)} title="Edit">
                                  <Edit />
                                </IconButton>
                                <IconButton size="small" color="error" onClick={() => handleDelete(row.id)} title="Delete">
                                  <Delete />
                                </IconButton>
                              </Box>
                            )}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>

              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                <Pagination
                  count={Math.ceil(filteredProducts.length / limit)}
                  page={page}
                  onChange={(event, value) => setPage(value)}
                  color="primary"
                  size="large"
                />
              </Box>
            </>
          )}
        </CardContent>
      </Card>

      {/* Add New Product Dialog */}
      <Dialog open={addDialogOpen} onClose={handleCloseAddDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <AddIcon color="primary" />
            <Typography variant="h6">Add New Product</Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
              {error}
            </Alert>
          )}
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Product Name *"
                value={newProduct.product_name}
                onChange={(e) => {
                  setNewProduct(prev => ({ ...prev, product_name: e.target.value }));
                }}
                variant="outlined"
                required
                placeholder="e.g., BRETHNOL SYP"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Product ID"
                type="number"
                value={newProduct.product_id}
                onChange={(e) => setNewProduct(prev => ({ ...prev, product_id: e.target.value }))}
                variant="outlined"
                helperText="Auto-generated if left empty"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Product Price"
                type="number"
                value={newProduct.product_price}
                onChange={(e) => setNewProduct(prev => ({ ...prev, product_price: e.target.value }))}
                variant="outlined"
                inputProps={{ step: '0.01', min: '0' }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseAddDialog} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleSaveNew} variant="contained" disabled={saving}>
            {saving ? 'Creating...' : 'Create Product'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProductGenerator;


