import { useQuery } from '@tanstack/react-query'
import { applicationsApi } from '@/services/api'
import { useNavigate } from 'react-router-dom'
import { FileText, Clock, CheckCircle, XCircle, AlertCircle, ChevronRight } from 'lucide-react'

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: any }> = {
  pending: { label: 'Pending', color: 'bg-yellow-100 text-yellow-700', icon: Clock },
  reviewing: { label: 'Reviewing', color: 'bg-blue-100 text-blue-700', icon: AlertCircle },
  shortlisted: { label: 'Shortlisted', color: 'bg-purple-100 text-purple-700', icon: AlertCircle },
  accepted: { label: 'Accepted', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  rejected: { label: 'Rejected', color: 'bg-red-100 text-red-700', icon: XCircle },
}

export default function MyApplications() {
  const navigate = useNavigate()

  const { data: applications = [], isLoading } = useQuery({
    queryKey: ['my-applications'],
    queryFn: async () => {
      const res = await applicationsApi.getMyApplications()
      return res.data
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-gray-200 rounded w-1/4 animate-pulse" />
        {[1, 2, 3].map(i => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-5 bg-gray-200 rounded w-1/3 mb-2" />
            <div className="h-4 bg-gray-100 rounded w-1/4" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">My Applications</h1>
        <span className="text-sm text-gray-500">{applications.length} total</span>
      </div>

      {/* Summary bar */}
      {applications.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {Object.entries(STATUS_CONFIG).map(([status, cfg]) => {
            const count = applications.filter((a: any) => a.status === status).length
            const Icon = cfg.icon
            return (
              <div key={status} className="bg-white rounded-lg shadow p-4 flex items-center gap-3">
                <div className={`p-2 rounded-full ${cfg.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-xs text-gray-500">{cfg.label}</p>
                  <p className="text-xl font-bold text-gray-900">{count}</p>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {applications.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">No applications yet</p>
          <p className="text-gray-400 text-sm mt-1">Browse jobs and start applying!</p>
          <button
            onClick={() => navigate('/jobs')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            Browse Jobs
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {applications.map((app: any) => {
            const cfg = STATUS_CONFIG[app.status] || STATUS_CONFIG.pending
            const Icon = cfg.icon
            return (
              <div
                key={app.id}
                onClick={() => navigate(`/applications/${app.id}`)}
                className="bg-white rounded-lg shadow p-5 hover:shadow-md transition-shadow cursor-pointer flex items-center justify-between gap-4"
              >
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 truncate">
                    {app.job?.title || `Job #${app.job_id}`}
                  </h3>
                  <p className="text-sm text-gray-500 mt-0.5">
                    {app.job?.company_name || 'Company'} · Applied {new Date(app.applied_at || app.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                  </p>
                  {app.match_score && (
                    <div className="mt-2 flex items-center gap-2">
                      <div className="h-1.5 w-24 bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 rounded-full" style={{ width: `${app.match_score}%` }} />
                      </div>
                      <span className="text-xs text-gray-500">Match: {app.match_score.toFixed(0)}%</span>
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <span className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${cfg.color}`}>
                    <Icon className="w-3.5 h-3.5" />
                    {cfg.label}
                  </span>
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
