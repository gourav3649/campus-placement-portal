import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../../services/api';
import { Application, ApplicationStatus } from '../../types';
import { ChevronLeft, Building, Calendar, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';
import { format } from 'date-fns';

export default function ApplicationDetails() {
  const { id } = useParams();
  const [app, setApp] = useState<Application | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchApp = async () => {
      try {
        const res = await api.get(`/applications/${id}`);
        setApp(res.data);
      } catch (err) {
        console.error("Failed to fetch application", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchApp();
  }, [id]);

  if (isLoading) return <div className="p-8">Loading application...</div>;
  if (!app) return <div className="p-8 text-center text-gray-500">Application not found.</div>;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Link to="/applications" className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors">
        <ChevronLeft size={16} className="mr-1"/> Back to Applications
      </Link>

      <div className="card p-8">
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-blue-100 text-blue-700 rounded-2xl flex items-center justify-center font-bold text-3xl">
              {app.job?.company_name?.charAt(0) || 'C'}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{app.job?.title || 'Unknown Role'}</h1>
              <p className="text-lg font-medium text-gray-600 flex items-center gap-2 mt-1">
                <Building size={18}/> {app.job?.company_name || 'Unknown Company'}
              </p>
            </div>
          </div>
          <span className={`badge status-${app.status} px-4 py-1.5 text-sm`}>{app.status}</span>
        </div>

        <div className="flex gap-6 mt-6 pt-6 border-t border-gray-100 text-sm">
          <div>
            <span className="block text-gray-500 mb-1">Applied On</span>
            <span className="font-semibold text-gray-900 flex items-center gap-1.5">
              <Calendar size={14} className="text-gray-400"/>
              {format(new Date(app.applied_at), 'MMM d, yyyy')}
            </span>
          </div>
          {!app.is_eligible && (
            <div className="text-red-600 bg-red-50 px-3 py-1.5 rounded-lg border border-red-100">
              <span className="font-bold flex items-center gap-1.5"><AlertTriangle size={14}/> Eligibility Failed</span>
              <p className="text-xs mt-0.5">{app.eligibility_reasons?.join(', ')}</p>
            </div>
          )}
        </div>
      </div>

      <h3 className="text-lg font-bold text-gray-900 mb-4 px-1">Application Timeline</h3>
      
      <div className="card p-0 overflow-hidden">
        <div className="p-6 space-y-8 relative">
          <div className="absolute left-10 top-10 bottom-10 w-px bg-gray-200" />

          {/* Applied Event */}
          <div className="relative flex items-start gap-6">
            <div className="w-8 h-8 rounded-full bg-blue-100 border-4 border-white z-10 flex items-center justify-center shrink-0 shadow-sm mt-1">
              <CheckCircle size={16} className="text-blue-600"/>
            </div>
            <div className="flex-1 bg-gray-50 p-4 rounded-xl border border-gray-100">
              <h4 className="font-bold text-gray-900">Application Submitted</h4>
              <p className="text-sm text-gray-500 mt-1">You successfully applied for this drive.</p>
              <p className="text-xs text-gray-400 mt-2">{format(new Date(app.applied_at), 'MMM d, yyyy h:mm a')}</p>
            </div>
          </div>

          {/* Dynamic Rounds */}
          {[...(app.rounds || [])].sort((a, b) => a.round_number - b.round_number).map((round, index, array) => {
            const isPassed = round.result === 'PASSED';
            const isFailed = round.result === 'FAILED';
            const isPending = round.result === 'PENDING';
            const isCurrent = index === array.length - 1; // Highlight the latest round
            
            return (
              <div key={round.id} className="relative flex items-start gap-6">
                <div className={`w-8 h-8 rounded-full border-4 border-white z-10 flex items-center justify-center shrink-0 shadow-sm mt-1 ${isPassed ? 'bg-green-100 text-green-600' : isFailed ? 'bg-red-100 text-red-600' : 'bg-yellow-100 text-yellow-600'} ${isCurrent ? 'ring-2 ring-blue-400 ring-offset-2' : ''}`}>
                  <span className="font-bold text-xs">{round.round_number}</span>
                </div>
                <div className="flex-1 bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-bold text-gray-900">{round.round_name}</h4>
                        {isCurrent && <span className="text-[10px] uppercase tracking-wider font-bold bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">Current Phase</span>}
                      </div>
                      <p className="text-sm text-gray-500 mt-0.5">Round {round.round_number}</p>
                    </div>
                    {isPassed && <span className="flex items-center gap-1 text-sm font-bold text-green-600 bg-green-50 px-2 py-1 rounded"><CheckCircle size={14}/> Passed</span>}
                    {isFailed && <span className="flex items-center gap-1 text-sm font-bold text-red-600 bg-red-50 px-2 py-1 rounded"><XCircle size={14}/> Failed</span>}
                    {isPending && <span className="flex items-center gap-1 text-sm font-bold text-yellow-600 bg-yellow-50 px-2 py-1 rounded"><Clock size={14}/> Pending</span>}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Final Status if explicitly set outside rounds */}
          {(app.status === ApplicationStatus.ACCEPTED || app.status === ApplicationStatus.REJECTED) && (
             <div className="relative flex items-start gap-6">
             <div className={`w-8 h-8 rounded-full border-4 border-white z-10 flex items-center justify-center shrink-0 shadow-sm mt-1 ${app.status === ApplicationStatus.ACCEPTED ? 'bg-green-500 text-white' : 'bg-red-500 text-white'}`}>
               {app.status === ApplicationStatus.ACCEPTED ? <CheckCircle size={16}/> : <XCircle size={16}/>}
             </div>
             <div className={`flex-1 p-5 rounded-xl border ${app.status === ApplicationStatus.ACCEPTED ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
               <h4 className={`font-bold text-lg ${app.status === ApplicationStatus.ACCEPTED ? 'text-green-800' : 'text-red-800'}`}>
                 {app.status === ApplicationStatus.ACCEPTED ? 'Congratulations! Offer Extended' : 'Application Rejected'}
               </h4>
               <p className={`text-sm mt-1 ${app.status === ApplicationStatus.ACCEPTED ? 'text-green-700' : 'text-red-700'}`}>
                 {app.status === ApplicationStatus.ACCEPTED ? 'You have successfully cleared all rounds and have been formally selected for this role.' : 'Unfortunately, you were not chosen to proceed further in this drive.'}
               </p>
             </div>
           </div>
          )}
        </div>
      </div>
    </div>
  );
}
