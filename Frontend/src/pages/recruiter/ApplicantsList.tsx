import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../../services/api';
import { Application, ApplicationStatus, Job } from '../../types';
import { Search, FileText, ChevronDown, ChevronRight, ChevronLeft } from 'lucide-react';

export default function ApplicantsList() {
  const { id } = useParams();
  const [apps, setApps] = useState<Application[]>([]);
  const [job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [branchFilter, setBranchFilter] = useState<string>('ALL');

  const [expandedRow, setExpandedRow] = useState<number | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [appsRes, jobRes] = await Promise.all([
          api.get(`/applications/recruiter/job/${id}`),
          api.get(`/jobs/${id}`) // Ensure recruiter has an endpoint to get their own job, or we can just use public endpoint.
        ]);
        setApps(appsRes.data);
        setJob(jobRes.data);
      } catch (err) {
        console.error("Failed to fetch applicants or job details", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [id]);

  const viewResume = (resumeId: number | undefined) => {
    if (!resumeId) {
      alert("No resume attached to this application.");
      return;
    }
    // Secure access would hit an endpoint like /api/v1/resumes/{resumeId} which verifies recruiter ownership of the drive
    alert(`Downloading/Viewing resume ID: ${resumeId}`);
  };

  // Derive unique branches for filter dropdown
  const uniqueBranches = Array.from(new Set(apps.map(a => a.student?.branch || 'Unknown')));

  const filteredApps = apps.filter(app => {
    const matchesSearch = app.student?.name.toLowerCase().includes(search.toLowerCase()) || 
                          app.student?.roll_number.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || app.status === statusFilter;
    const matchesBranch = branchFilter === 'ALL' || app.student?.branch === branchFilter;
    return matchesSearch && matchesStatus && matchesBranch;
  });

  if (isLoading) return <div className="p-8">Loading applicants...</div>;

  return (
    <div className="space-y-6">
      <Link to="/dashboard" className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors">
        <ChevronLeft size={16} className="mr-1"/> Back to Dashboard
      </Link>

      <div className="page-header items-end">
        <div>
          <h1 className="page-title">{job?.title || 'Drive'} Applicants</h1>
          <p className="text-sm text-gray-500 mt-1">Read-only view of all candidates and their current stage in your hiring funnel.</p>
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        {/* Toolbar */}
        <div className="bg-gray-50 p-4 border-b border-gray-200 flex flex-wrap gap-4 items-center justify-between">
          <div className="flex gap-4 flex-1">
            <div className="relative max-w-sm flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
              <input 
                type="text" 
                placeholder="Search name or roll no..." 
                value={search} onChange={e => setSearch(e.target.value)}
                className="input pl-9 !py-2 !text-sm"
              />
            </div>
            <select className="input !py-2 !text-sm w-40" value={branchFilter} onChange={e => setBranchFilter(e.target.value)}>
              <option value="ALL">All Branches</option>
              {uniqueBranches.map(b => <option key={b} value={b}>{b}</option>)}
            </select>
            <select className="input !py-2 !text-sm w-48" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
              <option value="ALL">All Statuses</option>
              <option value={ApplicationStatus.PENDING}>Pending</option>
              <option value={ApplicationStatus.SHORTLISTED}>Shortlisted</option>
              <option value={ApplicationStatus.ACCEPTED}>Placed (Accepted)</option>
              <option value={ApplicationStatus.REJECTED}>Rejected</option>
              <option value={ApplicationStatus.ELIGIBILITY_FAILED}>Ineligible</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white border-b border-gray-200">
                <th className="p-4 font-semibold text-gray-600 w-12 text-center"></th>
                <th className="p-4 font-semibold text-gray-600 text-sm">Student Name</th>
                <th className="p-4 font-semibold text-gray-600 text-sm">Roll No</th>
                <th className="p-4 font-semibold text-gray-600 text-sm">Branch</th>
                <th className="p-4 font-semibold text-gray-600 text-sm text-center">CGPA</th>
                <th className="p-4 font-semibold text-gray-600 text-sm">Status</th>
                <th className="p-4 font-semibold text-gray-600 text-sm">Latest Round</th>
                <th className="p-4 font-semibold text-gray-600 text-sm">Resume</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredApps.length === 0 ? (
                <tr><td colSpan={8} className="p-8 text-center text-gray-500">No applicants match criteria</td></tr>
              ) : (
                filteredApps.map(app => {
                  const s = app.student;
                  const isExpanded = expandedRow === app.id;
                  
                  // Compute latest round explicitly on frontend
                  const sortedRounds = app.rounds ? [...app.rounds].sort((a, b) => a.round_number - b.round_number) : [];
                  const latestRound = sortedRounds.length > 0 ? sortedRounds[sortedRounds.length - 1] : null;

                  return (
                    <React.Fragment key={app.id}>
                      <tr className={`hover:bg-gray-50 transition-colors`}>
                        <td className="p-4 text-center">
                          <button onClick={() => setExpandedRow(isExpanded ? null : app.id)} className="text-gray-400 hover:text-gray-600">
                            {isExpanded ? <ChevronDown size={18}/> : <ChevronRight size={18}/>}
                          </button>
                        </td>
                        <td className="p-4">
                          <div className="font-medium text-gray-900">{s?.name || 'Unknown'}</div>
                          {!app.is_eligible && <div className="text-[10px] text-red-500 mt-0.5" title={app.eligibility_reasons?.join(', ')}>Failed Eligibility</div>}
                        </td>
                        <td className="p-4 text-sm text-gray-600">{s?.roll_number}</td>
                        <td className="p-4 text-sm text-gray-600">{s?.branch}</td>
                        <td className="p-4 text-sm font-semibold text-center text-gray-700">{s?.cgpa?.toFixed(2)}</td>
                        <td className="p-4">
                          <span className={`badge status-${app.status}`}>{app.status}</span>
                        </td>
                        <td className="p-4">
                          {latestRound ? (
                            <div className="text-sm">
                              <div className="font-medium text-gray-800">{latestRound.round_name}</div>
                              <div className={`text-xs mt-0.5 font-medium ${latestRound.result === 'PASSED' ? 'text-green-600' : latestRound.result === 'FAILED' ? 'text-red-600' : 'text-yellow-600'}`}>
                                {latestRound.result}
                              </div>
                            </div>
                          ) : (
                            <span className="text-xs text-gray-400">No rounds yet</span>
                          )}
                        </td>
                        <td className="p-4">
                          <button 
                            onClick={() => viewResume(app.resume_id || undefined)} 
                            className="text-gray-400 hover:text-blue-600 p-1 flex items-center justify-center w-full" 
                            title="View Resume"
                          >
                            <FileText size={18} />
                          </button>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr>
                          <td colSpan={8} className="bg-gray-50/50 p-6 border-b border-gray-100">
                            <div className="max-w-2xl">
                              <h4 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wider">Round History</h4>
                              {sortedRounds.length === 0 ? (
                                <p className="text-sm text-gray-500">No rounds recorded for this student yet.</p>
                              ) : (
                                <div className="space-y-2">
                                  {sortedRounds.map((round) => (
                                    <div key={round.id} className="flex flex-wrap items-center justify-between p-3 bg-white border border-gray-200 rounded-lg">
                                      <div className="flex items-center gap-4">
                                        <div className="w-6 h-6 rounded bg-gray-100 text-gray-600 text-xs font-bold flex items-center justify-center">
                                          {round.round_number}
                                        </div>
                                        <span className="font-medium text-gray-900">{round.round_name}</span>
                                      </div>
                                      <div className="flex items-center gap-4">
                                        <span className={`text-sm font-bold ${round.result === 'PASSED' ? 'text-green-600' : round.result === 'FAILED' ? 'text-red-600' : 'text-yellow-600'}`}>
                                          {round.result}
                                        </span>
                                        {/* No delete button for recruiters */}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
