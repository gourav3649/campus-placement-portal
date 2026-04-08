import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../../services/api';
import { Application, ApplicationStatus } from '../../types';
import { Check, X, Search, FileText, Download, Briefcase, ListPlus, ChevronDown, ChevronRight, Trash2 } from 'lucide-react';

export default function DriveDetails() {
  const { id } = useParams();
  const [apps, setApps] = useState<Application[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [branchFilter, setBranchFilter] = useState<string>('ALL');

  const [selectedApps, setSelectedApps] = useState<Set<number>>(new Set());
  const [isBulkUpdating, setIsBulkUpdating] = useState(false);
  const [showRoundModal, setShowRoundModal] = useState(false);
  const [roundForm, setRoundForm] = useState({ round_name: '', round_number: 1, result: 'PENDING' });
  const [expandedRow, setExpandedRow] = useState<number | null>(null);

  const fetchApps = async () => {
    try {
      const res = await api.get(`/applications/job/${id}`);
      setApps(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchApps();
  }, [id]);

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedApps(new Set(filteredApps.map(a => a.id)));
    } else {
      setSelectedApps(new Set());
    }
  };

  const handleSelectOne = (appId: number) => {
    const newSet = new Set(selectedApps);
    if (newSet.has(appId)) newSet.delete(appId);
    else newSet.add(appId);
    setSelectedApps(newSet);
  };

  const bulkUpdateStatus = async (newStatus: ApplicationStatus) => {
    if (selectedApps.size === 0) return;
    if (!window.confirm(`Update ${selectedApps.size} applicants to ${newStatus}?`)) return;

    setIsBulkUpdating(true);
    try {
      const results = await Promise.allSettled(
        Array.from(selectedApps).map(appId => 
          api.put(`/applications/officer/${appId}/status?new_status=${newStatus}`)
        )
      );
      
      const succeeded = results.filter(r => r.status === 'fulfilled').length;
      const failed = results.filter(r => r.status === 'rejected').length;

      if (failed > 0) {
        alert(`Partial success: ${succeeded} updated, ${failed} failed.`);
      }

      setSelectedApps(new Set());
      await fetchApps();
    } catch (err) {
      alert("An unexpected error occurred during bulk update.");
      console.error(err);
    } finally {
      setIsBulkUpdating(false);
    }
  };

  const bulkAddRound = async () => {
    if (selectedApps.size === 0 || !roundForm.round_name) return;

    // Validation guard: filter out REJECTED, WITHDRAWN, or FAILED students
    const validApps = Array.from(selectedApps).filter(appId => {
      const app = apps.find(a => a.id === appId);
      if (!app) return false;
      if (app.status === ApplicationStatus.REJECTED || app.status === ApplicationStatus.WITHDRAWN) return false;
      if (app.rounds && app.rounds.length > 0 && app.rounds[app.rounds.length - 1].result === 'FAILED') return false;
      return true;
    });

    if (validApps.length === 0) {
      alert("None of the selected applicants are eligible for a new round (they are rejected or failed their previous round).");
      return;
    }

    if (validApps.length < selectedApps.size) {
      if (!window.confirm(`Only ${validApps.length} of ${selectedApps.size} applicants are eligible for the next round. Proceed formatting only the eligible ones?`)) return;
    }

    setIsBulkUpdating(true);
    try {
      const results = await Promise.allSettled(
        validApps.map(appId => 
          api.post(`/applications/${appId}/rounds`, roundForm)
        )
      );

      const succeeded = results.filter(r => r.status === 'fulfilled').length;
      const failed = results.filter(r => r.status === 'rejected').length;

      if (failed > 0) {
        alert(`Partial success: ${succeeded} rounds added, ${failed} failed.`);
      }

      setShowRoundModal(false);
      setSelectedApps(new Set());
      setRoundForm({ round_name: '', round_number: 1, result: 'PENDING' });
      await fetchApps();
    } catch (err) {
      alert("An unexpected error occurred during bulk assignment.");
    } finally {
      setIsBulkUpdating(false);
    }
  };

  const deleteRound = async (roundId: number) => {
    if (!window.confirm("Are you sure you want to delete this round entry?")) return;
    try {
      await api.delete(`/rounds/${roundId}`);
      await fetchApps();
    } catch (err) {
      alert("Failed to delete round.");
    }
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
      <div className="page-header items-end">
        <div>
          <h1 className="page-title">Manage Drive Applicants</h1>
          <p className="text-sm text-gray-500 mt-1">Replacement for Excel filtering. Send updates directly to student dashboards.</p>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary"><Download size={16}/> Export CSV</button>
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

          {selectedApps.size > 0 && (
            <div className="flex items-center gap-2 border-l border-gray-300 pl-4 py-1">
              <span className="text-sm font-medium text-blue-700 bg-blue-50 px-2 py-1 rounded">{selectedApps.size} selected</span>
              <button disabled={isBulkUpdating} onClick={() => setShowRoundModal(true)} className="btn-secondary !bg-indigo-100 !text-indigo-700 !py-1.5"><ListPlus size={14}/> Bulk Round</button>
              <button disabled={isBulkUpdating} onClick={() => bulkUpdateStatus(ApplicationStatus.SHORTLISTED)} className="btn-secondary !bg-purple-100 !text-purple-700 !py-1.5"><Check size={14}/> Bulk Shortlist</button>
              <button disabled={isBulkUpdating} onClick={() => bulkUpdateStatus(ApplicationStatus.REJECTED)} className="btn-secondary !bg-red-100 !text-red-700 !py-1.5"><X size={14}/> Bulk Reject</button>
            </div>
          )}
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white border-b border-gray-200">
                <th className="p-4 font-semibold text-gray-600 w-12 text-center"></th>
                <th className="p-4 font-semibold text-gray-600 w-12 text-center">
                  <input type="checkbox" onChange={handleSelectAll} checked={selectedApps.size > 0 && selectedApps.size === filteredApps.length} className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-600" />
                </th>
                <th className="p-4 font-semibold text-gray-600 text-sm">Student Name</th>
                <th className="p-4 font-semibold text-gray-600 text-sm">Roll No</th>
                <th className="p-4 font-semibold text-gray-600 text-sm">Branch</th>
                <th className="p-4 font-semibold text-gray-600 text-sm text-center">CGPA</th>
                <th className="p-4 font-semibold text-gray-600 text-sm">Status</th>
                <th className="p-4 font-semibold text-gray-600 text-sm">Latest Round</th>
                <th className="p-4 font-semibold text-gray-600 text-sm">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredApps.length === 0 ? (
                <tr><td colSpan={8} className="p-8 text-center text-gray-500">No applicants match criteria</td></tr>
              ) : (
                filteredApps.map(app => {
                  const s = app.student;
                  const isExpanded = expandedRow === app.id;
                  return (
                    <React.Fragment key={app.id}>
                      <tr className={`hover:bg-gray-50 transition-colors ${selectedApps.has(app.id) ? 'bg-blue-50/30' : ''}`}>
                        <td className="p-4 text-center">
                          <button onClick={() => setExpandedRow(isExpanded ? null : app.id)} className="text-gray-400 hover:text-gray-600">
                            {isExpanded ? <ChevronDown size={18}/> : <ChevronRight size={18}/>}
                          </button>
                        </td>
                        <td className="p-4 text-center">
                          <input type="checkbox" checked={selectedApps.has(app.id)} onChange={() => handleSelectOne(app.id)} className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-600" />
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
                          {app.rounds && app.rounds.length > 0 ? (
                            <div className="text-sm">
                              <div className="font-medium text-gray-800">{app.rounds[app.rounds.length - 1].round_name}</div>
                              <div className={`text-xs mt-0.5 font-medium ${app.rounds[app.rounds.length - 1].result === 'PASSED' ? 'text-green-600' : app.rounds[app.rounds.length - 1].result === 'FAILED' ? 'text-red-600' : 'text-yellow-600'}`}>
                                {app.rounds[app.rounds.length - 1].result}
                              </div>
                            </div>
                          ) : (
                            <span className="text-xs text-gray-400">No rounds yet</span>
                          )}
                        </td>
                        <td className="p-4">
                          <div className="flex gap-2">
                            <button className="text-gray-400 hover:text-blue-600 p-1" title="View Resume"><FileText size={18} /></button>
                            <button className="text-gray-400 hover:text-green-600 p-1" title="Record Offer"><Briefcase size={18} /></button>
                          </div>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr>
                          <td colSpan={9} className="bg-gray-50/50 p-6 border-b border-gray-100">
                            <div className="max-w-2xl">
                              <h4 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wider">Round History</h4>
                              {(!app.rounds || app.rounds.length === 0) ? (
                                <p className="text-sm text-gray-500">No rounds recorded for this student yet.</p>
                              ) : (
                                <div className="space-y-2">
                                  {app.rounds.map((round) => (
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
                                        <button onClick={() => deleteRound(round.id)} className="text-gray-400 hover:text-red-600 p-1" title="Delete Round Mistake">
                                          <Trash2 size={16} />
                                        </button>
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

      {/* Bulk Round Modal overlay */}
      {showRoundModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl border border-gray-100">
            <h3 className="text-lg font-bold mb-4">Add Round to {selectedApps.size} Applicants</h3>
            <div className="space-y-4">
              <div>
                <label className="label">Round Name</label>
                <input type="text" className="input" placeholder="e.g. Technical Interview" value={roundForm.round_name} onChange={e => setRoundForm({...roundForm, round_name: e.target.value})} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Round Number</label>
                  <input type="number" className="input" min="1" value={roundForm.round_number} onChange={e => setRoundForm({...roundForm, round_number: parseInt(e.target.value)})} />
                </div>
                <div>
                  <label className="label">Result</label>
                  <select className="input" value={roundForm.result} onChange={e => setRoundForm({...roundForm, result: e.target.value})}>
                    <option value="PENDING">Pending</option>
                    <option value="PASSED">Passed</option>
                    <option value="FAILED">Failed</option>
                    <option value="ABSENT">Absent</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button className="btn-ghost" onClick={() => setShowRoundModal(false)}>Cancel</button>
                <button className="btn-primary" disabled={isBulkUpdating || !roundForm.round_name} onClick={bulkAddRound}>
                  {isBulkUpdating ? 'Saving...' : 'Save Rounds'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
