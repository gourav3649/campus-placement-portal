import { useQuery } from '@tanstack/react-query'
import { studentsApi, recruitersApi, jobsApi, applicationsApi } from '@/services/api'
import { useNavigate } from 'react-router-dom'
import { Users, Building2, Briefcase, FileText, ChevronRight, TrendingUp } from 'lucide-react'

export default function AdminDashboard() {
  const navigate = useNavigate()

  const { data: students = [] } = useQuery({
    queryKey: ['admin-students'],
    queryFn: () => studentsApi.getAll().then(r => r.data),
  })
  const { data: recruiters = [] } = useQuery({
    queryKey: ['admin-recruiters'],
    queryFn: () => recruitersApi.getAll().then(r => r.data),
  })
  const { data: jobs = [] } = useQuery({
    queryKey: ['admin-jobs'],
    queryFn: () => jobsApi.getAll().then(r => r.data),
  })
  const { data: applications = [] } = useQuery({
    queryKey: ['admin-applications'],
    queryFn: () => applicationsApi.getAll().then(r => r.data),
  })

  const placed = Array.isArray(students) ? students.filter((s: any) => s.is_placed).length : 0
  const activeJobs = Array.isArray(jobs) ? jobs.filter((j: any) => j.is_active).length : 0
  const accepted = Array.isArray(applications) ? applications.filter((a: any) => a.status === 'accepted').length : 0

  const stats = [
    { label: 'Total Students', value: Array.isArray(students) ? students.length : 0, icon: Users, color: 'text-blue-600', bg: 'bg-blue-50', click: '/placement/students' },
    { label: 'Recruiters', value: Array.isArray(recruiters) ? recruiters.length : 0, icon: Building2, color: 'text-purple-600', bg: 'bg-purple-50', click: '/placement/recruiters' },
    { label: 'Active Jobs', value: activeJobs, icon: Briefcase, color: 'text-green-600', bg: 'bg-green-50', click: null },
    { label: 'Applications', value: Array.isArray(applications) ? applications.length : 0, icon: FileText, color: 'text-orange-600', bg: 'bg-orange-50', click: null },
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
      <p className="text-gray-500 text-sm mb-8">Full oversight of the Campus Placement Portal</p>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map(stat => (
          <div
            key={stat.label}
            onClick={() => stat.click && navigate(stat.click)}
            className={`bg-white rounded-lg shadow p-5 flex items-center gap-4 ${stat.click ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}`}
          >
            <div className={`p-3 rounded-xl ${stat.bg}`}>
              <stat.icon className={`w-6 h-6 ${stat.color}`} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Placement Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg shadow p-6 text-white">
          <TrendingUp className="w-8 h-8 mb-3 opacity-80" />
          <p className="text-3xl font-bold">{placed}</p>
          <p className="text-blue-100 text-sm mt-1">Students Placed</p>
          {Array.isArray(students) && students.length > 0 && (
            <p className="text-xs text-blue-200 mt-2">
              {((placed / students.length) * 100).toFixed(1)}% placement rate
            </p>
          )}
        </div>
        <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-lg shadow p-6 text-white">
          <Briefcase className="w-8 h-8 mb-3 opacity-80" />
          <p className="text-3xl font-bold">{activeJobs}</p>
          <p className="text-green-100 text-sm mt-1">Open Positions</p>
        </div>
        <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-lg shadow p-6 text-white">
          <Users className="w-8 h-8 mb-3 opacity-80" />
          <p className="text-3xl font-bold">{accepted}</p>
          <p className="text-purple-100 text-sm mt-1">Offers Accepted</p>
        </div>
      </div>

      {/* Quick Links */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-5 py-4 border-b">
          <h2 className="font-semibold text-gray-900">Quick Actions</h2>
        </div>
        <div className="divide-y">
          {[
            { label: 'Manage Students', desc: 'View and update student profiles', path: '/placement/students' },
            { label: 'Manage Recruiters', desc: 'View and update recruiter profiles', path: '/placement/recruiters' },
          ].map(item => (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors text-left"
            >
              <div>
                <p className="font-medium text-gray-900 text-sm">{item.label}</p>
                <p className="text-xs text-gray-500 mt-0.5">{item.desc}</p>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-400" />
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
