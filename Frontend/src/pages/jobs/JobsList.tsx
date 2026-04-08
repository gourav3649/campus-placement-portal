import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { Job, Application } from '../../types';
import { Link } from 'react-router-dom';
import { Briefcase, MapPin, Calendar, Clock, CheckCircle } from 'lucide-react';
import { format } from 'date-fns';

export default function JobsList() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [myApps, setMyApps] = useState<Application[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [jobsRes, appsRes] = await Promise.all([
          api.get('/jobs/'), // approved jobs for my college
          api.get('/applications/me') // my applications
        ]);
        setJobs(jobsRes.data);
        setMyApps(appsRes.data);
      } catch (err) {
        console.error("Failed to fetch jobs");
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  if (isLoading) return <div className="p-8">Loading drives...</div>;

  const getAppForJob = (jobId: number) => myApps.find(a => a.job_id === jobId);

  return (
    <div className="space-y-6">
      <div className="page-header">
        <h1 className="page-title">Campus Drives</h1>
        <p className="text-sm text-gray-500 mt-1">Browse and apply to companies hiring from your college.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {jobs.length === 0 ? (
          <div className="col-span-full p-12 text-center bg-gray-50 rounded-2xl border border-gray-200">
            <Briefcase className="mx-auto text-gray-400 mb-3" size={32} />
            <h3 className="text-lg font-medium text-gray-900">No active drives</h3>
            <p className="text-gray-500 mt-1">Check back later for new opportunities.</p>
          </div>
        ) : (
          jobs.map(job => {
            const app = getAppForJob(job.id);
            const isApplied = !!app;

            return (
              <div key={job.id} className={`card p-6 flex flex-col hover:border-blue-300 transition-colors ${isApplied ? 'bg-gray-50/50' : 'bg-white'}`}>
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors line-clamp-1">{job.title}</h3>
                    <p className="font-medium text-gray-600 mt-1 flex items-center gap-1.5"><Briefcase size={14}/> {job.company_name}</p>
                  </div>
                  {isApplied && (
                    <span className="flex items-center gap-1 bg-green-100 text-green-700 text-xs font-bold px-2.5 py-1 rounded-full whitespace-nowrap">
                      <CheckCircle size={12}/> Applied
                    </span>
                  )}
                </div>

                <div className="space-y-2 mt-2 flex-1">
                  {job.location && (
                    <div className="flex items-start gap-2 text-sm text-gray-600">
                      <MapPin size={16} className="mt-0.5 text-gray-400 shrink-0"/>
                      <span>{job.location}</span>
                    </div>
                  )}
                  {job.salary_package && (
                    <div className="flex items-start gap-2 text-sm text-gray-600 font-medium">
                      <span className="w-4 flex justify-center text-gray-400">₹</span>
                      <span>{job.salary_package}</span>
                    </div>
                  )}
                  {job.drive_date && (
                    <div className="flex items-start gap-2 text-sm text-gray-600">
                      <Calendar size={16} className="mt-0.5 text-gray-400 shrink-0"/>
                      <span>Drive: {format(new Date(job.drive_date), 'MMM d, yyyy')}</span>
                    </div>
                  )}
                  {job.deadline && (
                    <div className="flex items-start gap-2 text-sm text-red-600">
                      <Clock size={16} className="mt-0.5 shrink-0"/>
                      <span>Ends: {format(new Date(job.deadline), 'MMM d, h:mm a')}</span>
                    </div>
                  )}
                </div>

                <div className="mt-6 pt-4 border-t border-gray-100 flex items-center justify-between">
                  <div className="flex gap-2">
                    {job.min_cgpa && <span className="badge bg-gray-100 text-gray-600 text-xs">{job.min_cgpa}+ CGPA</span>}
                  </div>
                  <Link 
                    to={isApplied ? `/applications/${app.id}` : `/jobs/${job.id}`} 
                    className={`btn text-sm py-1.5 px-4 ${isApplied ? 'btn-secondary text-gray-700' : 'btn-primary'}`}
                  >
                    {isApplied ? 'View Status' : 'View Details'}
                  </Link>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
