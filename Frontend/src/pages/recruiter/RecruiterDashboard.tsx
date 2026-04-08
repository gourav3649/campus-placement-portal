import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { DriveStatus } from '../../types';
import { Link } from 'react-router-dom';
import { Briefcase, Users, Clock, Plus } from 'lucide-react';
import { format } from 'date-fns';

export default function RecruiterDashboard() {
  const [drives, setDrives] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDrives = async () => {
      try {
        const res = await api.get('/jobs/my-jobs');
        setDrives(res.data);
      } catch (err) {
        console.error("Failed to fetch recruiter drives", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchDrives();
  }, []);

  if (isLoading) return <div className="p-8">Loading your drives...</div>;

  return (
    <div className="space-y-6">
      <div className="page-header flex justify-between items-center pr-2">
        <div>
          <h1 className="page-title">My Campus Drives</h1>
          <p className="text-sm text-gray-500 mt-1">Manage your active postings and track applicant funnels.</p>
        </div>
        <Link to="/jobs/new" className="btn-primary flex items-center gap-2">
          <Plus size={18} /> Post New Drive
        </Link>
      </div>

      {drives.length === 0 ? (
        <div className="card p-12 flex flex-col items-center justify-center text-center border-dashed border-2 border-gray-200 bg-gray-50">
          <Briefcase size={40} className="text-gray-300 mb-4" />
          <h3 className="text-xl font-bold text-gray-800">No drives posted yet</h3>
          <p className="text-gray-500 mt-2 mb-6 max-w-sm">Create your first campus drive to start hiring students from this college.</p>
          <Link to="/jobs/new" className="btn-primary">Create Drive</Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {drives.map(drive => (
            <div key={drive.id} className="card p-0 flex flex-col hover:border-blue-300 transition-colors group">
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 line-clamp-1 group-hover:text-blue-600 transition-colors">
                      {drive.title}
                    </h3>
                    <p className="text-sm text-gray-500 mt-1 flex items-center gap-1.5">
                      <Clock size={14}/> 
                      {drive.drive_date ? format(new Date(drive.drive_date), 'MMM d, yyyy') : 'No drive date set'}
                    </p>
                  </div>
                  <span className={`badge status-${drive.status} shrink-0`}>{drive.status}</span>
                </div>

                <div className="grid grid-cols-3 gap-2 mt-6">
                  <div className="bg-gray-50 p-3 rounded-xl border border-gray-100 flex flex-col items-center justify-center text-center">
                    <span className="text-2xl font-bold text-gray-900">{drive.total_applied || 0}</span>
                    <span className="text-[10px] uppercase tracking-wider font-semibold text-gray-500 mt-1">Applied</span>
                  </div>
                  <div className="bg-blue-50 p-3 rounded-xl border border-blue-100 flex flex-col items-center justify-center text-center">
                    <span className="text-2xl font-bold text-blue-700">{drive.eligible_count || 0}</span>
                    <span className="text-[10px] uppercase tracking-wider font-semibold text-blue-600 mt-1">Eligible</span>
                  </div>
                  <div className="bg-green-50 p-3 rounded-xl border border-green-100 flex flex-col items-center justify-center text-center">
                    <span className="text-2xl font-bold text-green-700">{drive.selected_count || 0}</span>
                    <span className="text-[10px] uppercase tracking-wider font-semibold text-green-600 mt-1">Offers</span>
                  </div>
                </div>
              </div>

              <div className="mt-auto border-t border-gray-100 p-4 bg-gray-50/50 flex justify-between items-center rounded-b-2xl">
                {drive.status === DriveStatus.DRAFT ? (
                  <span className="text-xs font-medium text-amber-600 flex items-center gap-1.5">
                    <Clock size={14}/> Pending Placement Approval
                  </span>
                ) : (
                  <Link 
                    to={`/jobs/${drive.id}/applicants`} 
                    className="btn-secondary w-full justify-center gap-2"
                  >
                    <Users size={16}/> View Applicants
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
