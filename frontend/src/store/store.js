import { configureStore } from '@reduxjs/toolkit';
import authSlice from './slices/authSlice';
import uploadSlice from './slices/uploadSlice';
import analyticsSlice from './slices/analyticsSlice';
import transactionSlice from './slices/transactionSlice';
import recentUploadsSlice from './slices/recentUploadsSlice';
import unmatchedSlice from './slices/unmatchedSlice';
import dataQualitySlice from './slices/dataQualitySlice';

export default configureStore({
  reducer: {
    auth: authSlice,
    upload: uploadSlice,
    analytics: analyticsSlice,
    transactions: transactionSlice,
    recentUploads: recentUploadsSlice,
    unmatched: unmatchedSlice,
    dataQuality: dataQualitySlice,
  },
});