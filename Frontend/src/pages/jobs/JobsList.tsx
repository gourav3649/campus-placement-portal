import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { jobsApi, applicationsApi } from '@/services/api'
import { Briefcase, MapPin, DollarSign, Search, Filter, Clock, CheckCircle } from 'lucide-react'

export default function JobsList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [locationFilter, setLocationFilter] = useState('')
  const [applyingJobId, setApplyingJobId] = useState<number | null>(null)
  const [appliedJobs, setAppliedJobs] = useState<Set<number>>(new Set())
  const [successMsg, setSuccessMsg] = useState('')

  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ['jobs'],
    queryFn: async () => {
      const res = await jobsApi.getAll({ is_active: true })
      return res.data
    },
  })

  const applyMutation = useMutation({
    mutationFn: (jobId: number) =>
      applicationsApi.create({ job_id: jobId }),
    onSuccess: (_, jobId) => {
      setAppliedJobs(prev => new Set([...prev, jobId]))
      setApplyingJobId(null)
      setSuccessMsg('Application submitted successfully!')
      queryClient.invalidateQueries({ queryKey: ['my-applications'] })
      setTimeout(() => setSuccessMsg(''), 3000)
    },
    onError: () => setApplyingJobId(null),
  })

  const filtered = jobs.filter((job: any) => {
    const matchSearch = !search ||
      job.title?.toLowerCase().includes(search.toLowerCase()) ||
      job.company_name?.toLowerCase().includes(search.toLowerCase())
    const matchLocation = !locationFilter ||
      job.location?.toLowerCase().includes(locationFilter.toLowerCase())
    return matchSearch && matchLocation
  })

  const handleApply = (e: React.MouseEvent, jobId: number) => {
    e.stopPropagation()
    setApplyingJobId(jobId)
    applyMutation.mutate(jobId)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Available Jobs</h1>
        <span className="text-sm text-gray-500">{filtered.length} openings</span>
      </div>

      {successMsg && (
        <div className="mb-4 flex items-center gap-2 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">
          <CheckCircle className="w-4 h-4" />
          {successMsg}
        </div>
      )}

      {/* Search & Filter */}
      <div className="bg-white rounded-lg shadow p-4 mb-6 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by job title or company..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="relative sm:w-52">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Filter by location..."
            value={locationFilter}
            onChange={e => setLocationFilter(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Job Cards */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
              <div className="h-5 bg-gray-200 rounded w-1/3 mb-3" />
              <div className="h-4 bg-gray-100 rounded w-1/4 mb-4" />
              <div className="h-3 bg-gray-100 rounded w-full" />
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Briefcase className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">No jobs found</p>
          <p className="text-gray-400 text-sm mt-1">Try adjusting your search or filters</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((job: any) => (
            <div
              key={job.id}
              onClick={() => navigate(`/jobs/${job.id}`)}
              className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow cursor-pointer border border-transparent hover:border-blue-200"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <h2 className="text-lg font-semibold text-gray-900 truncate">{job.title}</h2>
                  <p className="text-blue-600 font-medium text-sm mt-0.5">{job.company_name}</p>

                  <div className="flex flex-wrap gap-4 mt-3 text-sm text-gray-500">
                    {job.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5" /> {job.location}
                      </span>
                    )}
                    {(job.salary_min || job.salary_max) && (
                      <span className="flex items-center gap-1">
                        <DollarSign className="w-3.5 h-3.5" />
                        ₹{job.salary_min}–{job.salary_max} LPA
                      </span>
                    )}
                    {job.job_type && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" /> {job.job_type}
                      </span>
                    )}
                  </div>

                  {job.required_skills && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {job.required_skills.split(',').slice(0, 5).map((skill: string) => (
                        <span key={skill} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full border border-blue-100">
                          {skill.trim()}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <button
                  onClick={e => handleApply(e, job.id)}
                  disabled={appliedJobs.has(job.id) || applyingJobId === job.id}
                  className={`shrink-0 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${appliedJobs.has(job.id)
                      ? 'bg-green-100 text-green-700 cursor-default'
                      : 'bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60'
                    }`}
                >
                  {applyingJobId === job.id ? 'Applying...' : appliedJobs.has(job.id) ? '✓ Applied' : 'Apply'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
