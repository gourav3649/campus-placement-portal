import { useQuery } from '@tanstack/react-query'
import { jobsApi, applicationsApi } from '@/services/api'
import { useAuth } from '@/context/AuthContext'
import { useNavigate } from 'react-router-dom'
import { Briefcase, Users, PlusCircle, ChevronRight, Eye } from 'lucide-react'

export default function RecruiterDashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const { data: myJobs = [], isLoading: jobsLoading } = useQuery({
    queryKey: ['recruiter-jobs'],
    queryFn: async () => {
      const res = await jobsApi.getAll({ recruiter_id: user?.id })
      return res.data
    },
  })

  const { data: allApplications = [], isLoading: appsLoading } = useQuery({
    queryKey: ['recruiter-applications'],
    queryFn: async () => {
      const res = await applicationsApi.getAll()
      return res.data
    },
  })

  const totalApps = allApplications.length
  const pendingApps = allApplications.filter((a: any) => a.status === 'pending').length
  const shortlisted = allApplications.filter((a: any) => a.status === 'shortlisted').length
  const activeJobs = myJobs.filter((j: any) => j.is_active).length

  const stats = [
    { label: 'Active Jobs', value: activeJobs, icon: Briefcase, color: 'bg-blue-500' },
    { label: 'Total Applications', value: totalApps, icon: Users, color: 'bg-indigo-500' },
    { label: 'Pending Review', value: pendingApps, icon: Eye, color: 'bg-yellow-500' },
    { label: 'Shortlisted', value: shortlisted, icon: Users, color: 'bg-green-500' },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Recruiter Dashboard</h1>
        <button
          onClick={() => navigate('/recruiter/jobs/post')}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          <PlusCircle className="w-4 h-4" /> Post a Job
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map(stat => (
          <div key={stat.label} className="bg-white rounded-lg shadow p-5 flex items-center gap-4">
            <div className={`p-3 rounded-full ${stat.color} bg-opacity-10`}>
              <stat.icon className={`w-5 h-5 ${stat.color.replace('bg-', 'text-')}`} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* My Job Postings */}
        <div className="bg-white rounded-lg shadow">
          <div className="flex items-center justify-between p-5 border-b">
            <h2 className="font-semibold text-gray-900">Your Job Postings</h2>
            <button onClick={() => navigate('/recruiter/jobs')} className="text-sm text-blue-600 hover:underline">
              View all
            </button>
          </div>
          {jobsLoading ? (
            <div className="p-5 space-y-3 animate-pulse">
              {[1, 2].map(i => <div key={i} className="h-10 bg-gray-100 rounded" />)}
            </div>
          ) : myJobs.length === 0 ? (
            <div className="p-10 text-center">
              <Briefcase className="w-10 h-10 text-gray-200 mx-auto mb-2" />
              <p className="text-sm text-gray-500">No jobs posted yet</p>
              <button
                onClick={() => navigate('/recruiter/jobs/post')}
                className="mt-3 text-sm text-blue-600 hover:underline"
              >
                Post your first job →
              </button>
            </div>
          ) : (
            <ul className="divide-y">
              {myJobs.slice(0, 5).map((job: any) => (
                <li
                  key={job.id}
                  onClick={() => navigate(`/recruiter/jobs/${job.id}/applications`)}
                  className="flex items-center justify-between p-4 hover:bg-gray-50 cursor-pointer"
                >
                  <div>
                    <p className="font-medium text-gray-900 text-sm">{job.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {job.applications_count ?? 0} applicants · {job.is_active ? '🟢 Active' : '⚫ Inactive'}
                    </p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Recent Applications */}
        <div className="bg-white rounded-lg shadow">
          <div className="flex items-center justify-between p-5 border-b">
            <h2 className="font-semibold text-gray-900">Recent Applications</h2>
            <button onClick={() => navigate('/recruiter/applications')} className="text-sm text-blue-600 hover:underline">
              View all
            </button>
          </div>
          {appsLoading ? (
            <div className="p-5 space-y-3 animate-pulse">
              {[1, 2, 3].map(i => <div key={i} className="h-10 bg-gray-100 rounded" />)}
            </div>
          ) : allApplications.length === 0 ? (
            <div className="p-10 text-center">
              <Users className="w-10 h-10 text-gray-200 mx-auto mb-2" />
              <p className="text-sm text-gray-500">No applications yet</p>
            </div>
          ) : (
            <ul className="divide-y">
              {allApplications.slice(0, 5).map((app: any) => (
                <li key={app.id} className="flex items-center justify-between p-4">
                  <div>
                    <p className="font-medium text-gray-900 text-sm">
                      {app.student?.first_name} {app.student?.last_name || `Student #${app.student_id}`}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {app.job?.title || `Job #${app.job_id}`}
                    </p>
                  </div>
                  <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${app.status === 'accepted' ? 'bg-green-100 text-green-700' :
                      app.status === 'rejected' ? 'bg-red-100 text-red-700' :
                        app.status === 'shortlisted' ? 'bg-purple-100 text-purple-700' :
                          'bg-yellow-100 text-yellow-700'
                    }`}>
                    {app.status}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
