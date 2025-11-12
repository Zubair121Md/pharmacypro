import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { recentUploadsAPI } from '../../services/api';

// Async thunks
export const fetchRecentUploads = createAsyncThunk(
  'recentUploads/fetchRecentUploads',
  async (_, { rejectWithValue }) => {
    try {
      const response = await recentUploadsAPI.getRecentUploads();
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch recent uploads');
    }
  }
);

export const fetchUploadDetails = createAsyncThunk(
  'recentUploads/fetchUploadDetails',
  async (uploadId, { rejectWithValue }) => {
    try {
      const response = await recentUploadsAPI.getUploadDetails(uploadId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch upload details');
    }
  }
);

export const exportUploadData = createAsyncThunk(
  'recentUploads/exportUploadData',
  async ({ uploadId, format }, { rejectWithValue }) => {
    try {
      const response = await recentUploadsAPI.exportUploadData(uploadId, format);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to export upload data');
    }
  }
);

export const deleteUpload = createAsyncThunk(
  'recentUploads/deleteUpload',
  async (uploadId, { rejectWithValue }) => {
    try {
      const response = await recentUploadsAPI.deleteUpload(uploadId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to delete upload');
    }
  }
);

const recentUploadsSlice = createSlice({
  name: 'recentUploads',
  initialState: {
    uploads: [],
    selectedUpload: null,
    loading: false,
    error: null,
  },
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    clearSelectedUpload: (state) => {
      state.selectedUpload = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch recent uploads
      .addCase(fetchRecentUploads.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRecentUploads.fulfilled, (state, action) => {
        state.loading = false;
        state.uploads = action.payload;
      })
      .addCase(fetchRecentUploads.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Fetch upload details
      .addCase(fetchUploadDetails.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUploadDetails.fulfilled, (state, action) => {
        state.loading = false;
        state.selectedUpload = action.payload;
      })
      .addCase(fetchUploadDetails.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Export upload data
      .addCase(exportUploadData.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(exportUploadData.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(exportUploadData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Delete upload
      .addCase(deleteUpload.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteUpload.fulfilled, (state, action) => {
        state.loading = false;
        // Remove the deleted upload from the list
        state.uploads = state.uploads.filter(upload => upload.id !== action.meta.arg);
      })
      .addCase(deleteUpload.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { clearError, clearSelectedUpload } = recentUploadsSlice.actions;
export default recentUploadsSlice.reducer;