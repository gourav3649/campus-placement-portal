import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { Application, ApplicationStatus } from '../../types';
import { Link } from 'react-router-dom';
import { Briefcase, ChevronRight, Clock, CheckCircle, XCircle } from 'lucide-react';
import { format } from 'date-fns';

export default function MyApplications() {
  const [apps, setApps] = useState<Application[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchApps = async () => {
      try {
        const res = await api.get('/applications/me');
        setApps(res.data);
      } catch (err) {
        console.error("Failed to fetch applications");
      } finally {
        setIsLoading(false);
      }
    };
    fetchApps();
  }, []);

  if (isLoading) return <div className="p-8">Loading applications...</div>;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="page-header">
        <h1 className="page-title">My Applications</h1>
        <p className="text-sm text-gray-500 mt-1">Track your progress and upcoming rounds for campus drives.</p>
      </div>

      <div className="space-y-4">
        {apps.length === 0 ? (
          <div className="p-12 text-center bg-gray-50 rounded-2xl border border-gray-200">
            <Briefcase className="mx-auto text-gray-400 mb-3" size={32} />
            <h3 className="text-lg font-medium text-gray-900">No applications yet</h3>
            <p className="text-gray-500 mt-1 mb-4">Start applying to campus drives to see your history here.</p>
            <Link to="/jobs" className="btn-primary">Browse Drives</Link>
          </div>
        ) : (
          apps.map(app => (
            <Link key={app.id} to={`/applications/${app.id}`} className="block card p-0 hover:border-blue-300 transition-colors group">
              <div className="p-5 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-start gap-4 flex-1">
                  <div className="w-12 h-12 shrink-0 bg-blue-100 text-blue-700 rounded-xl flex items-center justify-center font-bold text-xl">
                    {app.job?.company_name?.charAt(0) || 'C'}
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 group-hover:text-blue-600 transition-colors">{app.job?.title || 'Unknown Role'}</h3>
                    <p className="font-medium text-gray-600 mt-0.5">{app.job?.company_name || 'Unknown Company'}</p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                      <span>Applied: {format(new Date(app.applied_at), 'MMM d, yyyy')}</span>
                      {app.rounds && app.rounds.length > 0 && (
                        <>
                          <span className="w-1 h-1 rounded-full bg-gray-300"></span>
                          <span className="font-medium text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                            Latest Round: {app.rounds[app.rounds.length - 1].round_name}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between w-full sm:w-auto gap-4 pl-16 sm:pl-0 border-t sm:border-t-0 border-gray-100 pt-3 sm:pt-0">
                  <div className="flex items-center gap-2">
                    {app.status === ApplicationStatus.ACCEPTED && <CheckCircle className="text-green-500" size={18}/>}
                    {app.status === ApplicationStatus.REJECTED && <XCircle className="text-red-500" size={18}/>}
                    {app.status === ApplicationStatus.PENDING && <Clock className="text-yellow-500" size={18}/>}
                    <span className={`badge status-${app.status} text-sm`}>{app.status}</span>
                  </div>
                  <ChevronRight size={20} className="text-gray-300 group-hover:text-blue-500 transition-colors" />
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
