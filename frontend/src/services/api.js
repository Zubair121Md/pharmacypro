import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      // Log for debugging (especially useful in Tauri)
      if (config.url?.includes('reset-system')) {
        console.log('Reset system request - Token present:', !!token);
        console.log('Reset system request - Token value:', token.substring(0, 20) + '...');
        console.log('Reset system request - Full URL:', config.baseURL + config.url);
        console.log('Reset system request - Headers:', config.headers);
      }
    } else {
      console.warn('No token found in localStorage for request:', config.url);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (credentials) => {
    return api.post('/api/v1/auth/login', {
      username: credentials.username,
      password: credentials.password,
    }, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
  },
  signup: (userData) => api.post('/api/v1/auth/signup', userData),
  getCurrentUser: () => api.get('/api/v1/auth/me'),
};

// Upload API
export const uploadAPI = {
  uploadInvoice: (formData) => api.post('/api/v1/upload/invoice-only', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  uploadMaster: (formData) => api.post('/api/v1/upload/master-only', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  uploadEnhanced: (formData) => api.post('/api/v1/upload/enhanced', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
};

// Analytics API
export const analyticsAPI = {
  getDashboard: () => api.get('/api/v1/analytics/dashboard'),
  getRevenueByPharmacy: () => api.get('/api/v1/analytics/pharmacy-revenue'),
  getRevenueByDoctor: () => api.get('/api/v1/analytics/doctor-revenue'),
  getRevenueByRep: () => api.get('/api/v1/analytics/rep-revenue'),
  getRevenueByHQ: () => api.get('/api/v1/analytics/hq-revenue'),
  getRevenueByArea: () => api.get('/api/v1/analytics/area-revenue'),
  getRevenueByProduct: () => api.get('/api/v1/analytics/product-revenue'),
  getMonthlyTrends: () => api.get('/api/v1/analytics/trends'),
  getSummary: () => api.get('/api/v1/analytics/summary'),
  analyze: () => api.post('/api/v1/analytics/analyze'),
  clearCache: () => api.post('/api/v1/analytics/clear-cache'),
  clearRecentUploads: () => api.post('/api/v1/analytics/clear-recent-uploads'),
  setOverride: (analysisId, totalRevenue) => api.post('/api/v1/analytics/override', { analysis_id: analysisId, total_revenue: totalRevenue }),
  clearOverride: (analysisId) => api.delete('/api/v1/analytics/override', { params: { analysis_id: analysisId } }),
  exportMappedData: (format) => api.get('/api/v1/analytics/export-mapped-data', { 
    params: { format },
    responseType: 'blob'
  }),
  getMatchedResults: () => api.get('/api/v1/analytics/matched-results'),
  getDataQuality: () => api.get('/api/v1/analytics/data-quality'),
  exportDataQuality: (format) => api.get('/api/v1/analytics/data-quality/export', {
    params: { format },
    responseType: 'blob'
  }),
};

// Admin API
export const adminAPI = {
  getUsers: () => api.get('/api/v1/admin/users'),
  createUser: (userData) => api.post('/api/v1/admin/users', userData),
  updateUser: (id, userData) => api.put(`/api/v1/admin/users/${id}`, userData),
  deleteUser: (id) => api.delete(`/api/v1/admin/users/${id}`),
  getStats: () => api.get('/api/v1/admin/stats'),
  getAuditLogs: () => api.get('/api/v1/admin/audit-logs'),
  clearRecentUploads: () => api.post('/api/v1/admin/clear-recent-uploads'),
  resetSystem: () => api.post('/api/v1/admin/reset-system'),
  resetMasterData: () => api.post('/api/v1/admin/reset-master-data'),
};


// Transaction API
export const transactionAPI = {
  getTransactions: () => api.get('/api/v1/transactions'),
  addTransaction: (transactionData) => api.post('/api/v1/transactions', transactionData),
  updateTransaction: (id, transactionData) => api.put(`/api/v1/transactions/${id}`, transactionData),
  deleteTransaction: (id) => api.delete(`/api/v1/transactions/${id}`),
};

// Recent Uploads API
export const recentUploadsAPI = {
  getRecentUploads: () => api.get('/api/v1/uploads/recent'),
  getUploadDetails: (uploadId) => api.get(`/api/v1/uploads/${uploadId}/details`),
  exportUploadData: (uploadId, format) => api.get(`/api/v1/uploads/${uploadId}/export`, {
    params: { format },
    responseType: 'blob'
  }),
  deleteUpload: (uploadId) => api.delete(`/api/v1/uploads/${uploadId}`),
};

// Unmatched Records API
export const unmatchedAPI = {
  getUnmatchedRecords: () => api.get('/api/v1/unmatched'),
  mapRecord: (id, masterPharmacyId) => api.post(`/api/v1/unmatched/${id}/map`, { master_pharmacy_id: masterPharmacyId }),
  ignoreRecord: (id) => api.post(`/api/v1/unmatched/${id}/ignore`),
  getMasterPharmacies: (query = '') => api.get('/api/v1/unmatched/master-pharmacies', { params: { query } }),
  exportCSV: () => api.get('/api/v1/unmatched/export', { params: { format: 'csv' }, responseType: 'blob' }),
  exportExcel: () => api.get('/api/v1/unmatched/export', { params: { format: 'xlsx' }, responseType: 'blob' }),
};

// Newly Mapped Records API
export const newlyMappedAPI = {
  getNewlyMappedRecords: () => api.get('/api/v1/newly-mapped'),
  updateMapping: (recordId, masterPharmacyId) => api.put(`/api/v1/newly-mapped/${recordId}`, { master_pharmacy_id: masterPharmacyId }),
  deleteMapping: (recordId) => api.delete(`/api/v1/newly-mapped/${recordId}`),
};

// Master Data API
export const masterDataAPI = {
  getMasterData: (skip = 0, limit = 100) => api.get('/api/v1/master-data', { params: { skip, limit } }),
  createMasterData: (data) => api.post('/api/v1/master-data', data),
  updateMasterData: (recordId, updateData) => api.put(`/api/v1/master-data/${recordId}`, updateData),
  deleteMasterData: (recordId) => api.delete(`/api/v1/master-data/${recordId}`),
  exportExcel: () => api.get('/api/v1/master-data/export', { params: { format: 'xlsx' }, responseType: 'blob' }),
  exportCSV: () => api.get('/api/v1/master-data/export', { params: { format: 'csv' }, responseType: 'blob' }),
  getUniqueValues: () => api.get('/api/v1/master-data/unique-values'),
  getDuplicates: () => api.get('/api/v1/master-data/duplicates'),
};

// Split Rule API
export const splitRuleAPI = {
  getSplitRules: () => api.get('/api/v1/split-rules'),
  createSplitRule: (ruleData) => api.post('/api/v1/split-rules', ruleData),
  deleteSplitRule: (ruleId) => api.delete(`/api/v1/split-rules/${ruleId}`),
  exportExcel: () => api.get('/api/v1/split-rules/export', { params: { format: 'xlsx' }, responseType: 'blob' }),
  exportCSV: () => api.get('/api/v1/split-rules/export', { params: { format: 'csv' }, responseType: 'blob' }),
  importExcel: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/v1/split-rules/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

// Export API
export const exportAPI = {
  exportAnalyticsExcel: (params) => api.get('/api/v1/export/analytics-excel', { params }),
  exportRawDataExcel: (params) => api.get('/api/v1/export/raw-data-excel', { params }),
  exportRawDataCSV: (params) => api.get('/api/v1/export/raw-data-csv', { params }),
  exportAnalyticsPDF: (params) => api.get('/api/v1/export/analytics-pdf', { params }),
};

// ID Generator API
export const generatorAPI = {
  generateId: (name, type) => api.post('/api/v1/generator/generate', { name, type }),
  generateBatch: (requests) => api.post('/api/v1/generator/batch', requests),
  uploadProductReference: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/v1/generator/upload-product-reference', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

// Product Data API
export const productDataAPI = {
  getProducts: (skip = 0, limit = 100) => api.get('/api/v1/products', { params: { skip, limit } }),
  getAllProducts: () => api.get('/api/v1/products/all'),
  createProduct: (data) => api.post('/api/v1/products', data),
  updateProduct: (productId, updateData) => api.put(`/api/v1/products/${productId}`, updateData),
  deleteProduct: (productId) => api.delete(`/api/v1/products/${productId}`),
};

export default api;
