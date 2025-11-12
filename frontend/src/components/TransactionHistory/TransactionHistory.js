import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Chip,
  Grid,
  Fab,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Receipt as ReceiptIcon,
} from '@mui/icons-material';
import {
  fetchTransactions,
  deleteTransaction,
  addTransaction,
  updateTransaction,
} from '../../store/slices/transactionSlice';

function TransactionHistory() {
  const dispatch = useDispatch();
  const { transactions, loading, error } = useSelector((state) => state.transactions);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState(null);
  const [formData, setFormData] = useState({
    pharmacy_name: '',
    product: '',
    quantity: 0,
    amount: 0,
    doctor_name: '',
    rep_name: '',
    area: '',
    hq: '',
  });

  useEffect(() => {
    dispatch(fetchTransactions());
  }, [dispatch]);

  const handleOpenDialog = (transaction = null) => {
    if (transaction) {
      setEditingTransaction(transaction);
      setFormData({
        pharmacy_name: transaction.pharmacy_name || '',
        product: transaction.product || '',
        quantity: transaction.quantity || 0,
        amount: transaction.amount || 0,
        doctor_name: transaction.doctor_name || '',
        rep_name: transaction.rep_name || '',
        area: transaction.area || '',
        hq: transaction.hq || '',
      });
    } else {
      setEditingTransaction(null);
      setFormData({
        pharmacy_name: '',
        product: '',
        quantity: 0,
        amount: 0,
        doctor_name: '',
        rep_name: '',
        area: '',
        hq: '',
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingTransaction(null);
    setFormData({
      pharmacy_name: '',
      product: '',
      quantity: 0,
      amount: 0,
      doctor_name: '',
      rep_name: '',
      area: '',
      hq: '',
    });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'quantity' || name === 'amount' ? parseFloat(value) || 0 : value,
    }));
  };

  const handleSubmit = () => {
    if (editingTransaction) {
      dispatch(updateTransaction({ id: editingTransaction.id, ...formData }));
    } else {
      dispatch(addTransaction(formData));
    }
    handleCloseDialog();
  };

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this transaction?')) {
      dispatch(deleteTransaction(id));
    }
  };

  const handleRefresh = () => {
    dispatch(fetchTransactions());
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
          Transaction History
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            sx={{ mr: 2 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Add Transaction
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Card>
        <CardContent>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Pharmacy</TableCell>
                  <TableCell>Product</TableCell>
                  <TableCell align="right">Quantity</TableCell>
                  <TableCell align="right">Amount (₹)</TableCell>
                  <TableCell>Doctor</TableCell>
                  <TableCell>Rep</TableCell>
                  <TableCell>Area</TableCell>
                  <TableCell>HQ</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {transactions.map((transaction) => (
                  <TableRow key={transaction.id}>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        <ReceiptIcon sx={{ mr: 1, color: 'primary.main' }} />
                        {transaction.pharmacy_name}
                      </Box>
                    </TableCell>
                    <TableCell>{transaction.product}</TableCell>
                    <TableCell align="right">{transaction.quantity}</TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight="bold">
                        ₹{transaction.amount.toLocaleString('en-IN')}
                      </Typography>
                    </TableCell>
                    <TableCell>{transaction.doctor_name}</TableCell>
                    <TableCell>{transaction.rep_name}</TableCell>
                    <TableCell>
                      <Chip label={transaction.area} size="small" color="primary" variant="outlined" />
                    </TableCell>
                    <TableCell>
                      <Chip label={transaction.hq} size="small" color="secondary" variant="outlined" />
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(transaction)}
                        color="primary"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(transaction.id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Add/Edit Transaction Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingTransaction ? 'Edit Transaction' : 'Add New Transaction'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Pharmacy Name"
                name="pharmacy_name"
                value={formData.pharmacy_name}
                onChange={handleInputChange}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Product"
                name="product"
                value={formData.product}
                onChange={handleInputChange}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Quantity"
                name="quantity"
                type="number"
                value={formData.quantity}
                onChange={handleInputChange}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Amount (₹)"
                name="amount"
                type="number"
                value={formData.amount}
                onChange={handleInputChange}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Doctor Name"
                name="doctor_name"
                value={formData.doctor_name}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Rep Name"
                name="rep_name"
                value={formData.rep_name}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Area"
                name="area"
                value={formData.area}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="HQ"
                name="hq"
                value={formData.hq}
                onChange={handleInputChange}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingTransaction ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default TransactionHistory;

