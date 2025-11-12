import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { Box } from '@mui/material';
import { getCurrentUser } from './store/slices/authSlice';
import Layout from './components/Layout/Layout';
import Login from './components/Auth/Login';
import Dashboard from './components/Dashboard/Dashboard';
import FileUpload from './components/FileUpload/FileUpload';
import Analytics from './components/Analytics/Analytics';
import AdminPanel from './components/Admin/AdminPanel';
import Settings from './components/Settings/Settings';
import UnmatchedRecords from './components/DataManagement/UnmatchedRecords';
import RecentUploads from './components/RecentUploads/RecentUploads';
import IncompleteRecords from './components/DataManagement/IncompleteRecords';
import DataManagement from './components/DataManagement/DataManagement';
import MasterIdGenerator from './components/MasterIdGenerator/MasterIdGenerator';
import PharmacyGenerator from './components/MasterIdGenerator/PharmacyGenerator';
import ProductGenerator from './components/MasterIdGenerator/ProductGenerator';
import DoctorGenerator from './components/MasterIdGenerator/DoctorGenerator';
import ProtectedRoute from './components/Common/ProtectedRoute';
import RoleBasedComponent from './components/Common/RoleBasedComponent';

function App() {
  const dispatch = useDispatch();
  const { isAuthenticated, loading } = useSelector((state) => state.auth);

  useEffect(() => {
    if (localStorage.getItem('token')) {
      dispatch(getCurrentUser());
    }
  }, [dispatch]);

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        Loading...
      </Box>
    );
  }

  return (
    <Box>
      <Routes>
        <Route
          path="/login"
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />
          }
        />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="upload" element={<FileUpload />} />
          <Route path="analytics" element={<Analytics />} />
          <Route
            path="admin"
            element={
              <RoleBasedComponent allowedRoles={['admin', 'super_admin']}>
                <AdminPanel />
              </RoleBasedComponent>
            }
          />
          <Route path="settings" element={<Settings />} />
          <Route path="data-management" element={<DataManagement />} />
          <Route path="unmatched" element={<UnmatchedRecords />} />
          <Route path="incomplete" element={<IncompleteRecords />} />
          <Route path="recent-uploads" element={<RecentUploads />} />
          <Route path="generator" element={<MasterIdGenerator />} />
          <Route path="generator/pharmacy" element={<PharmacyGenerator />} />
          <Route path="generator/products" element={<ProductGenerator />} />
          <Route path="generator/doctor" element={<DoctorGenerator />} />
        </Route>
      </Routes>
    </Box>
  );
}

export default App;