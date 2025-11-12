import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { unmatchedAPI } from '../../services/api';

// Async thunks
export const fetchUnmatchedRecords = createAsyncThunk(
  'unmatched/fetchUnmatchedRecords',
  async (_, { rejectWithValue }) => {
    try {
      const response = await unmatchedAPI.getUnmatchedRecords();
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch unmatched records');
    }
  }
);

export const mapUnmatchedRecord = createAsyncThunk(
  'unmatched/mapUnmatchedRecord',
  async ({ recordId, pharmacyId }, { rejectWithValue }) => {
    try {
      const response = await unmatchedAPI.mapRecord(recordId, pharmacyId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to map record');
    }
  }
);

export const ignoreUnmatchedRecord = createAsyncThunk(
  'unmatched/ignoreUnmatchedRecord',
  async (recordId, { rejectWithValue }) => {
    try {
      const response = await unmatchedAPI.ignoreRecord(recordId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to ignore record');
    }
  }
);

export const exportUnmatchedRecords = createAsyncThunk(
  'unmatched/exportUnmatchedRecords',
  async (format, { rejectWithValue }) => {
    try {
      const response = await unmatchedAPI.exportUnmatchedRecords(format);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to export unmatched records');
    }
  }
);

const unmatchedSlice = createSlice({
  name: 'unmatched',
  initialState: {
    records: [],
    loading: false,
    error: null,
  },
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch unmatched records
      .addCase(fetchUnmatchedRecords.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUnmatchedRecords.fulfilled, (state, action) => {
        state.loading = false;
        state.records = action.payload;
      })
      .addCase(fetchUnmatchedRecords.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Map record
      .addCase(mapUnmatchedRecord.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(mapUnmatchedRecord.fulfilled, (state, action) => {
        state.loading = false;
        // Remove the mapped record from the list
        state.records = state.records.filter(record => record.id !== action.meta.arg.recordId);
      })
      .addCase(mapUnmatchedRecord.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Ignore record
      .addCase(ignoreUnmatchedRecord.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(ignoreUnmatchedRecord.fulfilled, (state, action) => {
        state.loading = false;
        // Remove the ignored record from the list
        state.records = state.records.filter(record => record.id !== action.meta.arg);
      })
      .addCase(ignoreUnmatchedRecord.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Export unmatched records
      .addCase(exportUnmatchedRecords.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(exportUnmatchedRecords.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(exportUnmatchedRecords.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { clearError } = unmatchedSlice.actions;
export default unmatchedSlice.reducer;
