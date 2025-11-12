import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { transactionAPI } from '../../services/api';

// Async thunks
export const fetchTransactions = createAsyncThunk(
  'transactions/fetchTransactions',
  async (_, { rejectWithValue }) => {
    try {
      const response = await transactionAPI.getTransactions();
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch transactions');
    }
  }
);

export const addTransaction = createAsyncThunk(
  'transactions/addTransaction',
  async (transactionData, { rejectWithValue }) => {
    try {
      const response = await transactionAPI.addTransaction(transactionData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to add transaction');
    }
  }
);

export const updateTransaction = createAsyncThunk(
  'transactions/updateTransaction',
  async ({ id, ...transactionData }, { rejectWithValue }) => {
    try {
      const response = await transactionAPI.updateTransaction(id, transactionData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to update transaction');
    }
  }
);

export const deleteTransaction = createAsyncThunk(
  'transactions/deleteTransaction',
  async (id, { rejectWithValue }) => {
    try {
      await transactionAPI.deleteTransaction(id);
      return id;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to delete transaction');
    }
  }
);

const initialState = {
  transactions: [],
  loading: false,
  error: null,
};

const transactionSlice = createSlice({
  name: 'transactions',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch transactions
      .addCase(fetchTransactions.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTransactions.fulfilled, (state, action) => {
        state.loading = false;
        state.transactions = action.payload;
      })
      .addCase(fetchTransactions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Add transaction
      .addCase(addTransaction.fulfilled, (state, action) => {
        state.transactions.push(action.payload);
      })
      .addCase(addTransaction.rejected, (state, action) => {
        state.error = action.payload;
      })
      // Update transaction
      .addCase(updateTransaction.fulfilled, (state, action) => {
        const index = state.transactions.findIndex(t => t.id === action.payload.id);
        if (index !== -1) {
          state.transactions[index] = action.payload;
        }
      })
      .addCase(updateTransaction.rejected, (state, action) => {
        state.error = action.payload;
      })
      // Delete transaction
      .addCase(deleteTransaction.fulfilled, (state, action) => {
        state.transactions = state.transactions.filter(t => t.id !== action.payload);
      })
      .addCase(deleteTransaction.rejected, (state, action) => {
        state.error = action.payload;
      });
  },
});

export const { clearError } = transactionSlice.actions;
export default transactionSlice.reducer;

