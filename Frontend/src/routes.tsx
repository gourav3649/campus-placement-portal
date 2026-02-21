import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'

// Layouts
import MainLayout from './layouts/MainLayout'
import AuthLayout from './layouts/AuthLayout'

// Public Pages
import Login from './pages/auth/Login'
import Register from './pages/auth/Register'

// Protected Pages
import Dashboard from './pages/Dashboard'
import StudentDashboard from './pages/student/StudentDashboard'
import RecruiterDashboard from './pages/recruiter/RecruiterDashboard'
import PlacementOfficerDashboard from './pages/placement/PlacementOfficerDashboard'
import AdminDashboard from './pages/admin/AdminDashboard'

// Job Pages
import JobsList from './pages/jobs/JobsList'
import JobDetails from './pages/jobs/JobDetails'
import CreateJob from './pages/jobs/CreateJob'
import PostJob from './pages/recruiter/PostJob'

// Application Pages
import MyApplications from './pages/applications/MyApplications'
import ApplicationDetails from './pages/applications/ApplicationDetails'

// Profile Pages
import Profile from './pages/profile/Profile'
import EditProfile from './pages/profile/EditProfile'

// Student Pages
import Students from './pages/students/Students'
import StudentDetails from './pages/students/StudentDetails'

// Recruiter Pages
import Recruiters from './pages/recruiters/Recruiters'
import RecruiterDetails from './pages/recruiters/RecruiterDetails'

// Error Pages
import NotFound from './pages/errors/NotFound'
import Unauthorized from './pages/errors/Unauthorized'

interface ProtectedRouteProps {
  children: React.ReactNode
  allowedRoles?: string[]
}

function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { user, isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />
  }

  return <>{children}</>
}

export default function AppRoutes() {
  const { user, isAuthenticated } = useAuth()

  // Redirect to role-specific dashboard
  const getDashboardRoute = () => {
    if (!user) return '/dashboard'

    switch (user.role) {
      case 'admin':
        return '/admin'
      case 'placement_officer':
        return '/placement'
      case 'student':
        return '/student'
      case 'recruiter':
        return '/recruiter'
      default:
        return '/dashboard'
    }
  }

  return (
    <Routes>
      {/* Public Routes */}
      <Route element={<AuthLayout />}>
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to={getDashboardRoute()} replace /> : <Login />}
        />
        <Route
          path="/register"
          element={isAuthenticated ? <Navigate to={getDashboardRoute()} replace /> : <Register />}
        />
      </Route>

      {/* Protected Routes */}
      <Route element={<MainLayout />}>
        {/* Common Routes */}
        <Route
          path="/"
          element={<Navigate to={isAuthenticated ? getDashboardRoute() : '/login'} replace />}
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile/edit"
          element={
            <ProtectedRoute>
              <EditProfile />
            </ProtectedRoute>
          }
        />

        {/* Student Routes */}
        <Route
          path="/student"
          element={
            <ProtectedRoute allowedRoles={['student']}>
              <StudentDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/jobs"
          element={
            <ProtectedRoute allowedRoles={['student']}>
              <JobsList />
            </ProtectedRoute>
          }
        />
        <Route
          path="/jobs/:id"
          element={
            <ProtectedRoute allowedRoles={['student']}>
              <JobDetails />
            </ProtectedRoute>
          }
        />
        <Route
          path="/applications"
          element={
            <ProtectedRoute allowedRoles={['student']}>
              <MyApplications />
            </ProtectedRoute>
          }
        />
        <Route
          path="/applications/:id"
          element={
            <ProtectedRoute allowedRoles={['student']}>
              <ApplicationDetails />
            </ProtectedRoute>
          }
        />

        {/* Recruiter Routes */}
        <Route
          path="/recruiter"
          element={
            <ProtectedRoute allowedRoles={['recruiter']}>
              <RecruiterDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/recruiter/jobs/create"
          element={
            <ProtectedRoute allowedRoles={['recruiter']}>
              <CreateJob />
            </ProtectedRoute>
          }
        />
        <Route
          path="/recruiter/jobs/post"
          element={
            <ProtectedRoute allowedRoles={['recruiter']}>
              <PostJob />
            </ProtectedRoute>
          }
        />

        {/* Placement Officer Routes */}
        <Route
          path="/placement"
          element={
            <ProtectedRoute allowedRoles={['placement_officer']}>
              <PlacementOfficerDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/placement/students"
          element={
            <ProtectedRoute allowedRoles={['placement_officer']}>
              <Students />
            </ProtectedRoute>
          }
        />
        <Route
          path="/placement/students/:id"
          element={
            <ProtectedRoute allowedRoles={['placement_officer']}>
              <StudentDetails />
            </ProtectedRoute>
          }
        />
        <Route
          path="/placement/recruiters"
          element={
            <ProtectedRoute allowedRoles={['placement_officer']}>
              <Recruiters />
            </ProtectedRoute>
          }
        />
        <Route
          path="/placement/recruiters/:id"
          element={
            <ProtectedRoute allowedRoles={['placement_officer']}>
              <RecruiterDetails />
            </ProtectedRoute>
          }
        />

        {/* Admin Routes */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Error Routes */}
      <Route path="/unauthorized" element={<Unauthorized />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
