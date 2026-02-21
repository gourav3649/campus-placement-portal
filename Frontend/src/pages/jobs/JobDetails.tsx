import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { jobsApi, applicationsApi } from '@/services/api'
import { ArrowLeft, MapPin, DollarSign, Clock, Briefcase, GraduationCap, CheckCircle } from 'lucide-react'
import { useState } from 'react'

export default function JobDetails() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [applied, setApplied] = useState(false)
  const [error, setError] = useState('')

  const { data: job, isLoading } = useQuery({
    queryKey: ['job', id],
    queryFn: async () => {
      const res = await jobsApi.getById(Number(id))
      return res.data
    },
    enabled: !!id,
  })

  const applyMutation = useMutation({
    mutationFn: () => applicationsApi.create({ job_id: Number(id) }),
    onSuccess: () => {
      setApplied(true)
      queryClient.invalidateQueries({ queryKey: ['my-applications'] })
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to apply. You may have already applied.')
    },
  })

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-1/3" />
        <div className="bg-white rounded-lg shadow p-6 space-y-3">
          <div className="h-6 bg-gray-200 rounded w-1/2" />
          <div className="h-4 bg-gray-100 rounded w-1/4" />
          <div className="h-20 bg-gray-100 rounded" />
        </div>
      </div>
    )
  }

  if (!job) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Job not found.</p>
        <button onClick={() => navigate('/jobs')} className="mt-4 text-blue-600 hover:underline text-sm">
          ← Back to Jobs
        </button>
      </div>
    )
  }

  return (
    <div>
      <button
        onClick={() => navigate('/jobs')}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Jobs
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h1 className="text-2xl font-bold text-gray-900">{job.title}</h1>
            <p className="text-blue-600 font-medium mt-1">{job.company_name}</p>

            <div className="flex flex-wrap gap-4 mt-4 text-sm text-gray-600">
              {job.location && <span className="flex items-center gap-1"><MapPin className="w-4 h-4" />{job.location}</span>}
              {job.job_type && <span className="flex items-center gap-1"><Clock className="w-4 h-4" />{job.job_type}</span>}
              {(job.salary_min || job.salary_max) && (
                <span className="flex items-center gap-1">
                  <DollarSign className="w-4 h-4" />₹{job.salary_min}–{job.salary_max} LPA
                </span>
              )}
              {job.experience_years !== undefined && (
                <span className="flex items-center gap-1">
                  <Briefcase className="w-4 h-4" />{job.experience_years}+ yrs experience
                </span>
              )}
              {job.education_level && (
                <span className="flex items-center gap-1">
                  <GraduationCap className="w-4 h-4" />{job.education_level}
                </span>
              )}
            </div>
          </div>

          {job.description && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Job Description</h2>
              <p className="text-gray-600 whitespace-pre-line leading-relaxed">{job.description}</p>
            </div>
          )}

          {job.requirements && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Requirements</h2>
              <p className="text-gray-600 whitespace-pre-line leading-relaxed">{job.requirements}</p>
            </div>
          )}

          {job.responsibilities && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Responsibilities</h2>
              <p className="text-gray-600 whitespace-pre-line leading-relaxed">{job.responsibilities}</p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow p-6">
            {applied ? (
              <div className="flex items-center gap-2 text-green-700 font-medium">
                <CheckCircle className="w-5 h-5" />
                Application Submitted!
              </div>
            ) : (
              <>
                {error && (
                  <div className="mb-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
                    {error}
                  </div>
                )}
                <button
                  onClick={() => applyMutation.mutate()}
                  disabled={applyMutation.isPending}
                  className="w-full py-2.5 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-60 transition-colors"
                >
                  {applyMutation.isPending ? 'Applying...' : 'Apply Now'}
                </button>
                <p className="text-xs text-gray-400 text-center mt-2">
                  Your profile will be shared with the recruiter
                </p>
              </>
            )}
          </div>

          {job.required_skills && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-semibold text-gray-900 mb-3">Required Skills</h3>
              <div className="flex flex-wrap gap-2">
                {job.required_skills.split(',').map((skill: string) => (
                  <span key={skill} className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full border border-blue-100">
                    {skill.trim()}
                  </span>
                ))}
              </div>
            </div>
          )}

          {job.min_cgpa && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-semibold text-gray-900 mb-2">Eligibility</h3>
              <p className="text-sm text-gray-600">Minimum CGPA: <span className="font-medium">{job.min_cgpa}</span></p>
              {job.allowed_branches && (
                <p className="text-sm text-gray-600 mt-1">Branches: <span className="font-medium">{job.allowed_branches}</span></p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
