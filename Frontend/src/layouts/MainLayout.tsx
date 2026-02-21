import { Outlet, Link } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { 
  LogOut, 
  LayoutDashboard, 
  Briefcase, 
  FileText, 
  User, 
  Users, 
  Building2 
} from 'lucide-react'

export default function MainLayout() {
  const { user, logout } = useAuth()

  const getNavItems = () => {
    const common = [
      { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/profile', icon: User, label: 'Profile' },
    ]

    switch (user?.role) {
      case 'student':
        return [
          { to: '/student', icon: LayoutDashboard, label: 'Dashboard' },
          { to: '/jobs', icon: Briefcase, label: 'Jobs' },
          { to: '/applications', icon: FileText, label: 'My Applications' },
          { to: '/profile', icon: User, label: 'Profile' },
        ]
      case 'recruiter':
        return [
          { to: '/recruiter', icon: LayoutDashboard, label: 'Dashboard' },
          { to: '/recruiter/jobs/create', icon: Briefcase, label: 'Post Job' },
          { to: '/profile', icon: User, label: 'Profile' },
        ]
      case 'placement_officer':
        return [
          { to: '/placement', icon: LayoutDashboard, label: 'Dashboard' },
          { to: '/placement/students', icon: Users, label: 'Students' },
          { to: '/placement/recruiters', icon: Building2, label: 'Recruiters' },
          { to: '/profile', icon: User, label: 'Profile' },
        ]
      case 'admin':
        return [
          { to: '/admin', icon: LayoutDashboard, label: 'Dashboard' },
          { to: '/profile', icon: User, label: 'Profile' },
        ]
      default:
        return common
    }
  }

  const navItems = getNavItems()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">
                Campus Placement Portal
              </h1>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">
                {user?.email}
              </span>
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-primary-100 text-primary-800">
                {user?.role?.replace('_', ' ').toUpperCase()}
              </span>
              <button
                onClick={logout}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex max-w-7xl mx-auto">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200 min-h-[calc(100vh-4rem)]">
          <nav className="p-4 space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="flex items-center gap-3 px-4 py-2 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-100 hover:text-gray-900 transition-colors"
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
