import { useQuery } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { applicationsApi } from '@/services/api'
import { ArrowLeft, Briefcase, Clock, CheckCircle, XCircle, AlertCircle, MapPin, DollarSign } from 'lucide-react'

const STATUS_STEPS = ['pending', 'reviewing', 'shortlisted', 'accepted']

const STATUS_META: Record<string, { label: string; color: string; icon: any }> = {
  pending: { label: 'Pending', color: 'text-yellow-600 bg-yellow-50 border-yellow-200', icon: Clock },
  reviewing: { label: 'Under Review', color: 'text-blue-600 bg-blue-50 border-blue-200', icon: AlertCircle },
  shortlisted: { label: 'Shortlisted', color: 'text-purple-600 bg-purple-50 border-purple-200', icon: AlertCircle },
  accepted: { label: 'Accepted', color: 'text-green-600 bg-green-50 border-green-200', icon: CheckCircle },
  rejected: { label: 'Rejected', color: 'text-red-600 bg-red-50 border-red-200', icon: XCircle },
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.min(100, Math.max(0, value))
  const color = pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-red-400'
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium text-gray-900">{pct.toFixed(0)}%</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function ApplicationDetails() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: app, isLoading } = useQuery({
    queryKey: ['application', id],
    queryFn: async () => {
      const res = await applicationsApi.getById(Number(id))
      return res.data
    },
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-6 bg-gray-200 rounded w-1/4" />
        <div className="bg-white rounded-lg shadow p-6 space-y-3">
          <div className="h-5 bg-gray-200 rounded w-1/2" />
          <div className="h-4 bg-gray-100 rounded w-1/3" />
          <div className="h-16 bg-gray-100 rounded" />
        </div>
      </div>
    )
  }

  if (!app) return (
    <div className="text-center py-12">
      <p className="text-gray-500">Application not found.</p>
      <button onClick={() => navigate('/applications')} className="mt-3 text-blue-600 hover:underline text-sm">← Back</button>
    </div>
  )

  const meta = STATUS_META[app.status] || STATUS_META.pending
  const StatusIcon = meta.icon
  const currentStep = STATUS_STEPS.indexOf(app.status)

  return (
    <div>
      <button onClick={() => navigate('/applications')} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6">
        <ArrowLeft className="w-4 h-4" /> Back to My Applications
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main column */}
        <div className="lg:col-span-2 space-y-5">
          {/* Job summary */}
          <div className="bg-white rounded-lg shadow p-6">
            <h1 className="text-xl font-bold text-gray-900">{app.job?.title || `Job #${app.job_id}`}</h1>
            <p className="text-blue-600 font-medium text-sm mt-0.5">{app.job?.company_name}</p>
            <div className="flex flex-wrap gap-4 mt-3 text-sm text-gray-500">
              {app.job?.location && <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" />{app.job.location}</span>}
              {(app.job?.salary_min || app.job?.salary_max) && (
                <span className="flex items-center gap-1"><DollarSign className="w-3.5 h-3.5" />₹{app.job.salary_min}–{app.job.salary_max} LPA</span>
              )}
              {app.job?.job_type && <span className="flex items-center gap-1"><Briefcase className="w-3.5 h-3.5" />{app.job.job_type}</span>}
            </div>
            <div className="mt-4">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium border ${meta.color}`}>
                <StatusIcon className="w-4 h-4" /> {meta.label}
              </span>
            </div>
          </div>

          {/* Application timeline */}
          {app.status !== 'rejected' && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="font-semibold text-gray-900 mb-4">Application Progress</h2>
              <div className="flex items-center gap-0">
                {STATUS_STEPS.map((step, i) => {
                  const done = i <= currentStep
                  const active = i === currentStep
                  return (
                    <div key={step} className="flex items-center flex-1 last:flex-none">
                      <div className="flex flex-col items-center">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border-2 ${done ? 'bg-blue-600 border-blue-600 text-white' : 'bg-white border-gray-300 text-gray-400'
                          } ${active ? 'ring-4 ring-blue-100' : ''}`}>
                          {done ? '✓' : i + 1}
                        </div>
                        <p className="text-xs text-gray-500 mt-1 capitalize whitespace-nowrap">{STATUS_META[step]?.label}</p>
                      </div>
                      {i < STATUS_STEPS.length - 1 && (
                        <div className={`flex-1 h-0.5 mx-1 ${i < currentStep ? 'bg-blue-600' : 'bg-gray-200'}`} />
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* AI Summary */}
          {app.ai_summary && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="font-semibold text-gray-900 mb-3">✨ AI Match Analysis</h2>
              <p className="text-gray-700 text-sm leading-relaxed mb-4">{app.ai_summary}</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {app.strengths?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-green-700 mb-2">💪 Strengths</h3>
                    <ul className="space-y-1">
                      {app.strengths.map((s: string, i: number) => (
                        <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                          <span className="text-green-500 mt-0.5">✓</span> {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {app.weaknesses?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-red-700 mb-2">⚡ Areas to Improve</h3>
                    <ul className="space-y-1">
                      {app.weaknesses.map((w: string, i: number) => (
                        <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                          <span className="text-red-400 mt-0.5">!</span> {w}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {app.recruiter_notes && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="font-semibold text-gray-900 mb-2">Recruiter Notes</h2>
              <p className="text-gray-600 text-sm">{app.recruiter_notes}</p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Match Score</h3>
            {app.match_score !== undefined ? (
              <div className="space-y-4">
                <div className="text-center mb-4">
                  <p className="text-4xl font-bold text-blue-600">{app.match_score.toFixed(0)}</p>
                  <p className="text-xs text-gray-500 mt-0.5">Overall Match / 100</p>
                </div>
                <ScoreBar label="Skills Match" value={app.skills_score ?? 0} />
                <ScoreBar label="Experience Match" value={app.experience_score ?? 0} />
                <ScoreBar label="Semantic Fit" value={app.semantic_score ?? 0} />
              </div>
            ) : (
              <p className="text-sm text-gray-500">Score not yet calculated.</p>
            )}
          </div>

          <div className="bg-white rounded-lg shadow p-6 space-y-3">
            <h3 className="font-semibold text-gray-900">Timeline</h3>
            <div>
              <p className="text-xs text-gray-500">Applied On</p>
              <p className="text-sm text-gray-900">
                {new Date(app.applied_at || app.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
              </p>
            </div>
            {app.updated_at && (
              <div>
                <p className="text-xs text-gray-500">Last Updated</p>
                <p className="text-sm text-gray-900">
                  {new Date(app.updated_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
                </p>
              </div>
            )}
          </div>

          <button
            onClick={() => app.job_id && navigate(`/jobs/${app.job_id}`)}
            className="w-full py-2.5 border border-blue-600 text-blue-600 text-sm font-medium rounded-lg hover:bg-blue-50 transition-colors"
          >
            View Job Posting →
          </button>
        </div>
      </div>
    </div>
  )
}
