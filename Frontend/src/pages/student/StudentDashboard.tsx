import { useQuery } from '@tanstack/react-query'
import { jobsApi, applicationsApi } from '@/services/api'
import { Briefcase, FileText, CheckCircle, Clock } from 'lucide-react'

export default function StudentDashboard() {
  const { data: jobs, isLoading: jobsLoading } = useQuery({
    queryKey: ['jobs'],
    queryFn: async () => {
      const response = await jobsApi.getAll({ is_active: true })
      return response.data
    },
  })

  const { data: applications } = useQuery({
    queryKey: ['my-applications'],
    queryFn: async () => {
      const response = await applicationsApi.getMyApplications()
      return response.data
    },
  })

  const stats = [
    {
      label: 'Available Jobs',
      value: jobs?.length || 0,
      icon: Briefcase,
      color: 'bg-blue-100 text-blue-600',
    },
    {
      label: 'My Applications',
      value: applications?.length || 0,
      icon: FileText,
      color: 'bg-purple-100 text-purple-600',
    },
    {
      label: 'Accepted',
      value: applications?.filter((app: any) => app.status === 'accepted').length || 0,
      icon: CheckCircle,
      color: 'bg-green-100 text-green-600',
    },
    {
      label: 'Pending',
      value: applications?.filter((app: any) => app.status === 'pending').length || 0,
      icon: Clock,
      color: 'bg-yellow-100 text-yellow-600',
    },
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Student Dashboard</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.label}</p>
                <p className="mt-2 text-3xl font-bold text-gray-900">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-full ${stat.color}`}>
                <stat.icon className="w-6 h-6" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Jobs */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Job Openings</h2>
        </div>
        <div className="p-6">
          {jobsLoading ? (
            <p className="text-gray-500">Loading jobs...</p>
          ) : jobs && jobs.length > 0 ? (
            <div className="space-y-4">
              {jobs.slice(0, 5).map((job: any) => (
                <div key={job.id} className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 transition-colors">
                  <h3 className="font-semibold text-gray-900">{job.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{job.company_name}</p>
                  <div className="flex gap-4 mt-2 text-xs text-gray-500">
                    <span>Location: {job.location}</span>
                    <span>Package: ₹{job.salary_min} - ₹{job.salary_max} LPA</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No jobs available at the moment.</p>
          )}
        </div>
      </div>
    </div>
  )
}
