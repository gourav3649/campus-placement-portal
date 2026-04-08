import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { Role } from './types';

// Layouts
import AuthLayout from './layouts/AuthLayout';
import MainLayout from './layouts/MainLayout';

// Auth Pages
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';

// Phase 2F
import PlacementOfficerDashboard from './pages/placement/PlacementOfficerDashboard';
import DriveDetails from './pages/placement/DriveDetails';
import RecruiterDashboard from './pages/recruiter/RecruiterDashboard';
import ApplicantsList from './pages/recruiter/ApplicantsList';

// Phase 3F
import JobsList from './pages/jobs/JobsList';
import JobDetails from './pages/jobs/JobDetails';
import MyApplications from './pages/applications/MyApplications';
import ApplicationDetails from './pages/applications/ApplicationDetails';

// Dummy Pages (to be implemented)
const Dashboard = () => <div className="p-6">Dashboard coming soon...</div>;
const NotFound = () => <div className="p-6">404 - Not Found</div>;

// Role guard wrapper
function ProtectedRoute({ children, allowedRoles }: { children: React.ReactNode, allowedRoles?: Role[] }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (allowedRoles && !allowedRoles.includes(user.role)) return <Navigate to="/unauthorized" replace />;
  return children;
}

export default function AppRoutes() {
  const { user } = useAuth();

  return (
    <Routes>
      {/* Public Routes */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <Login />} />
        <Route path="/register" element={user ? <Navigate to="/dashboard" replace /> : <Register />} />
      </Route>

      {/* Protected Routes */}
      <Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        {/* Dynamic Route to Correct Dashboard */}
        <Route path="/dashboard" element={
          user?.role === Role.PLACEMENT_OFFICER ? <PlacementOfficerDashboard /> : 
          user?.role === Role.RECRUITER ? <RecruiterDashboard /> :
          <Dashboard />
        } />
        
        {/* Placement Officer specific routes */}
        <Route path="/jobs/:id/manage" element={
          <ProtectedRoute allowedRoles={[Role.PLACEMENT_OFFICER]}>
            <DriveDetails />
          </ProtectedRoute>
        } />

        {/* Recruiter specific routes */}
        <Route path="/jobs/:id/applicants" element={
          <ProtectedRoute allowedRoles={[Role.RECRUITER]}>
            <ApplicantsList />
          </ProtectedRoute>
        } />

        {/* Student specific routes */}
        <Route path="/jobs" element={
          <ProtectedRoute allowedRoles={[Role.STUDENT]}><JobsList /></ProtectedRoute>
        } />
        <Route path="/jobs/:id" element={
          <ProtectedRoute allowedRoles={[Role.STUDENT]}><JobDetails /></ProtectedRoute>
        } />
        <Route path="/applications" element={
          <ProtectedRoute allowedRoles={[Role.STUDENT]}><MyApplications /></ProtectedRoute>
        } />
        <Route path="/applications/:id" element={
          <ProtectedRoute allowedRoles={[Role.STUDENT]}><ApplicationDetails /></ProtectedRoute>
        } />
      </Route>

      {/* Fallback */}
      <Route path="/unauthorized" element={<div className="p-6">403 - Unauthorized</div>} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
