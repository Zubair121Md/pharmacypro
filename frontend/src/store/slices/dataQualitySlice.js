import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { analyticsAPI } from '../../services/api';

// Async thunks
export const fetchDataQuality = createAsyncThunk(
  'dataQuality/fetchDataQuality',
  async (_, { rejectWithValue }) => {
    try {
      const response = await analyticsAPI.getDataQuality();
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch data quality');
    }
  }
);

export const exportDataQuality = createAsyncThunk(
  'dataQuality/exportDataQuality',
  async (format, { rejectWithValue }) => {
    try {
      const response = await analyticsAPI.exportDataQuality(format);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to export data quality');
    }
  }
);

const dataQualitySlice = createSlice({
  name: 'dataQuality',
  initialState: {
    dataQuality: null,
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
      // Fetch data quality
      .addCase(fetchDataQuality.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDataQuality.fulfilled, (state, action) => {
        state.loading = false;
        state.dataQuality = action.payload;
      })
      .addCase(fetchDataQuality.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Export data quality
      .addCase(exportDataQuality.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(exportDataQuality.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(exportDataQuality.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { clearError } = dataQualitySlice.actions;
export default dataQualitySlice.reducer;
