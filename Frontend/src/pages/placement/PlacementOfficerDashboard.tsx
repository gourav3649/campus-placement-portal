import { useQuery } from '@tanstack/react-query'
import { studentsApi, jobsApi, applicationsApi } from '@/services/api'
import { useNavigate } from 'react-router-dom'
import { Users, Briefcase, TrendingUp, ChevronRight, Search } from 'lucide-react'
import { useState } from 'react'

export default function PlacementOfficerDashboard() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')

  const { data: students = [], isLoading: studentsLoading } = useQuery({
    queryKey: ['po-students'],
    queryFn: () => studentsApi.getAll().then(r => r.data),
  })
  const { data: jobs = [] } = useQuery({
    queryKey: ['po-jobs'],
    queryFn: () => jobsApi.getAll({ is_active: true }).then(r => r.data),
  })
  const { data: applications = [] } = useQuery({
    queryKey: ['po-applications'],
    queryFn: () => applicationsApi.getAll().then(r => r.data),
  })

  const studentsArr = Array.isArray(students) ? students : []
  const placed = studentsArr.filter((s: any) => s.is_placed).length
  const unplaced = studentsArr.length - placed

  const filteredStudents = studentsArr.filter((s: any) => {
    const name = `${s.first_name} ${s.last_name}`.toLowerCase()
    return !search || name.includes(search.toLowerCase()) || s.enrollment_number?.includes(search)
  })

  const stats = [
    { label: 'Total Students', value: studentsArr.length, icon: Users, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Placed', value: placed, icon: TrendingUp, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'Unplaced', value: unplaced, icon: Users, color: 'text-yellow-600', bg: 'bg-yellow-50' },
    { label: 'Active Jobs', value: Array.isArray(jobs) ? jobs.length : 0, icon: Briefcase, color: 'text-purple-600', bg: 'bg-purple-50' },
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Placement Officer Dashboard</h1>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map(stat => (
          <div key={stat.label} className="bg-white rounded-lg shadow p-5 flex items-center gap-4">
            <div className={`p-3 rounded-xl ${stat.bg}`}>
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Students list */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow">
          <div className="p-5 border-b flex items-center justify-between gap-3">
            <h2 className="font-semibold text-gray-900">Students</h2>
            <div className="relative flex-1 max-w-xs">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search by name or enroll no."
                className="w-full pl-8 pr-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          {studentsLoading ? (
            <div className="p-5 space-y-3 animate-pulse">
              {[1, 2, 3].map(i => <div key={i} className="h-10 bg-gray-100 rounded" />)}
            </div>
          ) : (
            <div className="divide-y max-h-[480px] overflow-y-auto">
              {filteredStudents.slice(0, 30).map((s: any) => (
                <div
                  key={s.id}
                  onClick={() => navigate(`/placement/students/${s.id}`)}
                  className="flex items-center justify-between px-5 py-3.5 hover:bg-gray-50 cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-semibold text-sm">
                      {s.first_name?.[0]?.toUpperCase() || '?'}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{s.first_name} {s.last_name}</p>
                      <p className="text-xs text-gray-500">{s.enrollment_number} · {s.branch || s.major || 'N/A'}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${s.is_placed ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {s.is_placed ? 'Placed' : 'Unplaced'}
                    </span>
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  </div>
                </div>
              ))}
              {filteredStudents.length === 0 && (
                <div className="p-10 text-center text-sm text-gray-500">No students found</div>
              )}
            </div>
          )}
        </div>

        {/* Right panel */}
        <div className="space-y-4">
          {/* Placement rate card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-semibold text-gray-900 mb-3">Placement Rate</h3>
            <div className="flex items-end gap-2 mb-2">
              <p className="text-4xl font-bold text-blue-600">
                {studentsArr.length > 0 ? ((placed / studentsArr.length) * 100).toFixed(1) : 0}%
              </p>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all"
                style={{ width: `${studentsArr.length > 0 ? (placed / studentsArr.length) * 100 : 0}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-2">{placed} of {studentsArr.length} students placed</p>
          </div>

          {/* Recent applications */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-5 py-4 border-b flex justify-between items-center">
              <h3 className="font-semibold text-gray-900">Recent Applications</h3>
              <span className="text-xs text-gray-400">{Array.isArray(applications) ? applications.length : 0} total</span>
            </div>
            <div className="divide-y max-h-64 overflow-y-auto">
              {(Array.isArray(applications) ? applications : []).slice(0, 8).map((a: any) => (
                <div key={a.id} className="px-5 py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900 truncate">{a.job?.title || `Job #${a.job_id}`}</p>
                    <p className="text-xs text-gray-500">{a.student?.first_name} {a.student?.last_name}</p>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${a.status === 'accepted' ? 'bg-green-100 text-green-700' :
                    a.status === 'rejected' ? 'bg-red-100 text-red-700' :
                      a.status === 'shortlisted' ? 'bg-purple-100 text-purple-700' :
                        'bg-yellow-100 text-yellow-600'
                    }`}>
                    {a.status}
                  </span>
                </div>
              ))}
              {(!applications || applications.length === 0) && (
                <div className="p-6 text-center text-sm text-gray-500">No applications yet</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
