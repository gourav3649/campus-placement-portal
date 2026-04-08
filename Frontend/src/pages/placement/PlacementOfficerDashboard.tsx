import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { DriveStatus, JobType } from '../../types';
import { Link } from 'react-router-dom';
import { Briefcase, Users, CheckCircle, Search } from 'lucide-react';
import { format } from 'date-fns';

interface JobStats {
  id: number;
  title: string;
  job_type: JobType;
  status: DriveStatus;
  deadline?: string;
  drive_date?: string;
  total_applied: number;
  eligible_count: number;
  selected_count: number;
}

export default function PlacementOfficerDashboard() {
  const [drives, setDrives] = useState<JobStats[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');

  const fetchDrives = async () => {
    try {
      const res = await api.get('/jobs/all');
      setDrives(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDrives();
  }, []);

  const approveDrive = async (id: number) => {
    if (!window.confirm('Approve this drive? Students will be notified instantly.')) return;
    try {
      await api.post(`/jobs/${id}/approve`);
      fetchDrives();
    } catch (err) {
      alert('Failed to approve. Make sure the recruiter is verified first.');
    }
  };

  const filteredDrives = drives.filter(d => 
    d.title.toLowerCase().includes(search.toLowerCase())
  );

  if (isLoading) return <div className="p-8">Loading dashboard...</div>;

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title">Placement Drives Overview</h1>
          <p className="text-sm text-gray-500 mt-1">Manage ongoing placements and applicant rounds</p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input 
              type="text" 
              placeholder="Search drives..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input pl-10 w-64"
            />
          </div>
        </div>
      </div>

      {filteredDrives.length === 0 ? (
        <div className="card text-center py-12 text-gray-500">No drives found.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDrives.map(drive => (
            <div key={drive.id} className="card hover:shadow-md transition-shadow flex flex-col">
              <div className="flex justify-between items-start mb-4">
                <div className="badge status-APPROVED">{drive.status}</div>
                <div className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">
                  {drive.job_type.replace('_', ' ')}
                </div>
              </div>
              
              <h3 className="text-lg font-bold text-gray-900 mb-1">{drive.title}</h3>
              {drive.drive_date && (
                <p className="text-sm text-gray-500 mb-4">
                  Drive Date: <span className="font-medium text-gray-700">{format(new Date(drive.drive_date), 'dd MMM yyyy')}</span>
                </p>
              )}

              <div className="grid grid-cols-3 gap-2 mt-auto mb-6">
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="flex items-center justify-center text-gray-500 mb-1"><Users size={16}/></div>
                  <div className="text-lg font-bold text-gray-900">{drive.total_applied}</div>
                  <div className="text-[10px] text-gray-500 font-medium uppercase tracking-wider">Applied</div>
                </div>
                <div className="bg-blue-50 rounded-lg p-3 text-center">
                  <div className="flex items-center justify-center text-blue-500 mb-1"><CheckCircle size={16}/></div>
                  <div className="text-lg font-bold text-blue-900">{drive.eligible_count}</div>
                  <div className="text-[10px] text-blue-600 font-medium uppercase tracking-wider">Eligible</div>
                </div>
                <div className="bg-green-50 rounded-lg p-3 text-center">
                  <div className="flex items-center justify-center text-green-500 mb-1"><Briefcase size={16}/></div>
                  <div className="text-lg font-bold text-green-900">{drive.selected_count}</div>
                  <div className="text-[10px] text-green-700 font-medium uppercase tracking-wider">Offers</div>
                </div>
              </div>

              {drive.status === DriveStatus.DRAFT ? (
                <button 
                  onClick={() => approveDrive(drive.id)}
                  className="btn-primary w-full justify-center !py-2.5"
                >
                  Review & Approve
                </button>
              ) : (
                <Link to={`/jobs/${drive.id}/manage`} className="btn-secondary w-full justify-center !py-2.5">
                  Manage Workplace
                </Link>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
