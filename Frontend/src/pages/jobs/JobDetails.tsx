import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../../services/api';
import { Job, Application } from '../../types';
import { ChevronLeft, Building, Calendar, Clock, FileText, CheckCircle, AlertCircle, MapPin } from 'lucide-react';
import { format } from 'date-fns';

export default function JobDetails() {
  const { id } = useParams();
  const [job, setJob] = useState<Job | null>(null);
  const [application, setApplication] = useState<Application | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isApplying, setIsApplying] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [jobRes, appsRes] = await Promise.all([
          api.get(`/jobs/${id}`),
          api.get('/applications/me')
        ]);
        setJob(jobRes.data);
        const app = appsRes.data.find((a: Application) => a.job_id === Number(id));
        if (app) setApplication(app);
      } catch (err) {
        console.error("Failed to fetch job", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [id]);

  const handleApply = async () => {
    setIsApplying(true);
    setError('');
    try {
      const res = await api.post('/applications/', { job_id: Number(id) });
      setApplication(res.data);
      alert('Application submitted successfully!');
    } catch (err: any) {
      if (err.response?.status === 409) {
        // Stale frontend state, already applied
        alert("You have already applied to this drive.");
        // We can mimic an application object just to flip the UI to 'Already Applied'
        setApplication({ id: 0, job_id: Number(id), applied_at: new Date().toISOString() } as any);
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Failed to apply. Please try again.');
      }
    } finally {
      setIsApplying(false);
    }
  };

  if (isLoading) return <div className="p-8">Loading details...</div>;
  if (!job) return <div className="p-8 text-center text-gray-500">Drive not found or unavailable.</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Link to="/jobs" className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors">
        <ChevronLeft size={16} className="mr-1"/> Back to drives
      </Link>

      {/* Main Header Card */}
      <div className="card p-8">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 bg-blue-100 text-blue-700 rounded-xl flex items-center justify-center font-bold text-xl">
                {job.company_name.charAt(0)}
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{job.title}</h1>
                <p className="text-lg font-medium text-gray-600 flex items-center gap-2 mt-1">
                  <Building size={18}/> {job.company_name}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-4 mt-6">
              {job.location && (
                <div className="flex items-center gap-2 text-gray-600 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-100">
                  <MapPin size={16} className="text-gray-400"/>
                  <span className="text-sm font-medium">{job.location}</span>
                </div>
              )}
              {job.salary_package && (
                <div className="flex items-center gap-2 text-gray-600 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-100">
                  <span className="w-4 flex justify-center text-gray-400 font-bold">₹</span>
                  <span className="text-sm font-medium">{job.salary_package}</span>
                </div>
              )}
              {job.drive_date && (
                <div className="flex items-center gap-2 text-indigo-700 bg-indigo-50 px-3 py-1.5 rounded-lg border border-indigo-100">
                  <Calendar size={16} className="text-indigo-500"/>
                  <span className="text-sm font-bold">Drive: {format(new Date(job.drive_date), 'MMM d, yyyy')}</span>
                </div>
              )}
            </div>
          </div>

          <div className="sm:w-64 shrink-0 bg-gray-50 rounded-xl p-5 border border-gray-100 flex flex-col items-center text-center">
            {application ? (
              <>
                <div className="w-12 h-12 rounded-full bg-green-100 text-green-600 flex items-center justify-center mb-3">
                  <CheckCircle size={24} />
                </div>
                <h3 className="font-bold text-gray-900 mb-1">Already Applied</h3>
                <p className="text-xs text-gray-500 mb-4">You applied on {format(new Date(application.applied_at), 'MMM d, yyyy')}</p>
                <Link to={`/applications/${application.id}`} className="btn-secondary w-full">Track Status</Link>
              </>
            ) : (
              <>
                <h3 className="font-bold text-gray-900 mb-2">Ready to apply?</h3>
                {job.deadline && (
                  <p className="text-xs text-red-600 font-medium flex items-center justify-center gap-1.5 mb-4">
                    <Clock size={12}/> Closes {format(new Date(job.deadline), 'MMM d')}
                  </p>
                )}
                {error && (
                  <div className="text-xs text-red-600 bg-red-50 p-2 rounded mb-3 w-full text-left flex gap-1.5 items-start">
                    <AlertCircle size={14} className="shrink-0 mt-0.5"/>
                    <span>{error}</span>
                  </div>
                )}
                <button 
                  onClick={handleApply} 
                  disabled={isApplying}
                  className="btn-primary w-full text-base py-2.5"
                >
                  {isApplying ? 'Checking Eligibility...' : 'Apply Now'}
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-8">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2"><FileText size={18} className="text-blue-600"/> Job Description</h3>
            <div className="prose prose-sm prose-blue max-w-none text-gray-600 whitespace-pre-wrap">
              {job.description || "No detailed description provided by the recruiter."}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card p-6">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4 border-b border-gray-100 pb-2">Eligibility Criteria</h3>
            <ul className="space-y-4">
              <li className="flex justify-between items-center text-sm">
                <span className="text-gray-500">Min CGPA</span>
                <span className="font-bold text-gray-900">{job.min_cgpa || 'None'}</span>
              </li>
              <li className="flex justify-between items-center text-sm">
                <span className="text-gray-500">Max Backlogs</span>
                <span className="font-bold text-gray-900">{job.max_backlogs !== null ? job.max_backlogs : 'Not specified'}</span>
              </li>
              <li className="flex justify-between items-center text-sm">
                <span className="text-gray-500">Allowed Branches</span>
                <span className="font-medium text-gray-900 text-right max-w-[120px]">{job.allowed_branches ? job.allowed_branches.join(', ') : 'All Branches'}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
