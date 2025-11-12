import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { analyticsAPI } from '../../services/api';

// Helper function to safely extract error message
const getErrorMessage = (error, fallback) => {
  const detail = error.response?.data?.detail;
  if (typeof detail === 'string') {
    return detail;
  } else if (detail && typeof detail === 'object') {
    return JSON.stringify(detail);
  }
  return fallback;
};

// Async thunks
export const fetchDashboardData = createAsyncThunk(
  'analytics/fetchDashboardData',
  async (_, { rejectWithValue }) => {
    try {
      const response = await analyticsAPI.getDashboard();
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, 'Failed to fetch dashboard data'));
    }
  }
);

export const fetchRevenueByPharmacy = createAsyncThunk(
  'analytics/fetchRevenueByPharmacy',
  async (_, { rejectWithValue }) => {
    try {
      const response = await analyticsAPI.getRevenueByPharmacy();
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, 'Failed to fetch pharmacy revenue'));
    }
  }
);

export const fetchRevenueByDoctor = createAsyncThunk(
  'analytics/fetchRevenueByDoctor',
  async (_, { rejectWithValue }) => {
    try {
      const response = await analyticsAPI.getRevenueByDoctor();
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, 'Failed to fetch doctor revenue'));
    }
  }
);

export const fetchRevenueByRep = createAsyncThunk(
  'analytics/fetchRevenueByRep',
  async (_, { rejectWithValue }) => {
    try {
      const response = await analyticsAPI.getRevenueByRep();
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, 'Failed to fetch rep revenue'));
    }
  }
);

export const fetchRevenueByHQ = createAsyncThunk(
  'analytics/fetchRevenueByHQ',
  async (_, { rejectWithValue }) => {
    try {
      const response = await analyticsAPI.getRevenueByHQ();
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, 'Failed to fetch HQ revenue'));
    }
  }
);

export const fetchRevenueByArea = createAsyncThunk(
  'analytics/fetchRevenueByArea',
  async (_, { rejectWithValue }) => {
    try {
      const response = await analyticsAPI.getRevenueByArea();
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, 'Failed to fetch area revenue'));
    }
  }
);

export const fetchRevenueByProduct = createAsyncThunk(
  'analytics/fetchRevenueByProduct',
  async (_, { rejectWithValue }) => {
    try {
      const response = await analyticsAPI.getRevenueByProduct();
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, 'Failed to fetch product revenue'));
    }
  }
);

export const fetchMonthlyTrends = createAsyncThunk(
  'analytics/fetchMonthlyTrends',
  async (_, { rejectWithValue }) => {
    try {
      const response = await analyticsAPI.getMonthlyTrends();
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, 'Failed to fetch monthly trends'));
    }
  }
);

export const clearAnalyticsCache = createAsyncThunk(
  'analytics/clearAnalyticsCache',
  async (_, { rejectWithValue }) => {
    try {
      const response = await analyticsAPI.clearCache();
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, 'Failed to clear cache'));
    }
  }
);

export const resetAnalyticsState = createAsyncThunk(
  'analytics/resetAnalyticsState',
  async () => {
    // This is a synchronous action, no API call needed
    return {};
  }
);

const analyticsSlice = createSlice({
  name: 'analytics',
  initialState: {
    dashboardData: null,
    revenueByPharmacy: [],
    revenueByDoctor: [],
    revenueByRep: [],
    revenueByHQ: [],
    revenueByArea: [],
    revenueByProduct: [],
    monthlyTrends: [],
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
      // Dashboard data
      .addCase(fetchDashboardData.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDashboardData.fulfilled, (state, action) => {
        state.loading = false;
        state.dashboardData = action.payload;
      })
      .addCase(fetchDashboardData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Pharmacy revenue
      .addCase(fetchRevenueByPharmacy.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRevenueByPharmacy.fulfilled, (state, action) => {
        state.loading = false;
        state.revenueByPharmacy = action.payload;
      })
      .addCase(fetchRevenueByPharmacy.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Doctor revenue
      .addCase(fetchRevenueByDoctor.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRevenueByDoctor.fulfilled, (state, action) => {
        state.loading = false;
        state.revenueByDoctor = action.payload;
      })
      .addCase(fetchRevenueByDoctor.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Rep revenue
      .addCase(fetchRevenueByRep.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRevenueByRep.fulfilled, (state, action) => {
        state.loading = false;
        state.revenueByRep = action.payload;
      })
      .addCase(fetchRevenueByRep.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // HQ revenue
      .addCase(fetchRevenueByHQ.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRevenueByHQ.fulfilled, (state, action) => {
        state.loading = false;
        state.revenueByHQ = action.payload;
      })
      .addCase(fetchRevenueByHQ.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Area revenue
      .addCase(fetchRevenueByArea.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRevenueByArea.fulfilled, (state, action) => {
        state.loading = false;
        state.revenueByArea = action.payload;
      })
      .addCase(fetchRevenueByArea.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Product revenue
      .addCase(fetchRevenueByProduct.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRevenueByProduct.fulfilled, (state, action) => {
        state.loading = false;
        state.revenueByProduct = action.payload;
      })
      .addCase(fetchRevenueByProduct.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Monthly trends
      .addCase(fetchMonthlyTrends.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMonthlyTrends.fulfilled, (state, action) => {
        state.loading = false;
        state.monthlyTrends = action.payload;
      })
      .addCase(fetchMonthlyTrends.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Clear cache
      .addCase(clearAnalyticsCache.fulfilled, (state) => {
        state.dashboardData = null;
        state.revenueByPharmacy = [];
        state.revenueByDoctor = [];
        state.revenueByRep = [];
        state.revenueByHQ = [];
        state.revenueByArea = [];
        state.revenueByProduct = [];
        state.monthlyTrends = [];
        state.error = null;
      })
      // Reset state
      .addCase(resetAnalyticsState.fulfilled, (state) => {
        state.dashboardData = null;
        state.revenueByPharmacy = [];
        state.revenueByDoctor = [];
        state.revenueByRep = [];
        state.revenueByHQ = [];
        state.revenueByArea = [];
        state.revenueByProduct = [];
        state.monthlyTrends = [];
        state.loading = false;
        state.error = null;
      });
  },
});

export const { clearError } = analyticsSlice.actions;
export default analyticsSlice.reducer;
