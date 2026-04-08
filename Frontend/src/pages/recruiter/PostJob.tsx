import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { api } from '../../services/api';
import { College } from '../../types';
import { ChevronLeft, Info, CheckCircle } from 'lucide-react';

const jobSchema = z.object({
  title: z.string().min(2, 'Role/Job title is required'),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  job_type: z.enum(['FULL_TIME', 'INTERNSHIP', 'CONTRACT']),
  college_id: z.coerce.number().min(1, 'Please select a target college'),
  drive_date: z.string().optional().nullable(),
  reporting_time: z.string().optional().nullable(),
  min_cgpa: z.coerce.number().min(0).max(10).optional().or(z.literal('')),
  max_backlogs: z.coerce.number().min(0).optional().or(z.literal('')),
  allowed_branches: z.string().optional().nullable(),
});

type JobFormValues = z.infer<typeof jobSchema>;

export default function PostJob() {
  const navigate = useNavigate();
  const [colleges, setColleges] = useState<College[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<JobFormValues>({
    resolver: zodResolver(jobSchema),
    defaultValues: {
      job_type: 'FULL_TIME',
      college_id: 0,
    }
  });

  useEffect(() => {
    const fetchColleges = async () => {
      try {
        const res = await api.get('/colleges/');
        setColleges(res.data);
      } catch (err) {
        console.error('Failed to fetch colleges for drive creation', err);
      }
    };
    fetchColleges();
  }, []);

  const onSubmit = async (data: JobFormValues) => {
    setIsSubmitting(true);
    try {
      // Data reshaping for backend compliance.
      // Notice `exclude_placed_students` is implicitly left out, meaning backend defaults it to True.
      const payload = {
        title: data.title,
        description: data.description,
        job_type: data.job_type,
        college_id: data.college_id,
        drive_date: data.drive_date ? new Date(data.drive_date).toISOString() : null, // Backend expects datetime
        reporting_time: data.reporting_time || null,
        min_cgpa: data.min_cgpa === '' ? null : data.min_cgpa,
        max_backlogs: data.max_backlogs === '' ? null : data.max_backlogs,
        allowed_branches: data.allowed_branches 
                            ? data.allowed_branches.split(',').map(s => s.trim().toUpperCase()).filter(Boolean) 
                            : null,
      };

      await api.post('/jobs/', payload);
      setIsSuccess(true);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create drive. Check your permissions.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="max-w-2xl mx-auto mt-12">
        <div className="card text-center p-12">
          <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle size={40} />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Drive Created Successfully!</h2>
          <p className="text-gray-600 mb-8 max-w-sm mx-auto">
            Your drive has been saved as a <strong>DRAFT</strong>. It will become visible to students once approved by the Placement Officer.
          </p>
          <div className="flex gap-4 justify-center">
            <Link to="/dashboard" className="btn-primary">Return to Dashboard</Link>
            <button onClick={() => { setIsSuccess(false); window.scrollTo(0, 0); }} className="btn-secondary">Post Another Drive</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Link to="/dashboard" className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors">
        <ChevronLeft size={16} className="mr-1"/> Back to Dashboard
      </Link>

      <div className="page-header items-end">
        <div>
          <h1 className="page-title">Post New Campus Drive</h1>
          <p className="text-sm text-gray-500 mt-1">Create a new job posting for students. Must be approved before going live.</p>
        </div>
      </div>

      <div className="bg-yellow-50 text-yellow-800 p-4 rounded-xl border border-yellow-200 flex gap-3 text-sm">
        <Info className="shrink-0 text-yellow-600" size={20} />
        <div>
          <strong className="font-bold">Pending Approval Required:</strong> All newly created drives are automatically saved as <strong>DRAFT</strong>. You will not receive any applications until a Placement Officer reviews and approves your drive.
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
        {/* Core Details */}
        <div className="card p-6 space-y-5">
          <h3 className="text-lg font-bold border-b border-gray-100 pb-2">Core Information</h3>
          
          <div>
            <label className="label">Target College *</label>
            <select className="input" {...register('college_id')}>
              <option value="0">Select a college...</option>
              {colleges.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            {errors.college_id && <p className="text-red-500 text-xs mt-1">{errors.college_id.message}</p>}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label className="label">Role / Job Title *</label>
              <input type="text" className="input" placeholder="e.g. Software Engineer" {...register('title')} />
              {errors.title && <p className="text-red-500 text-xs mt-1">{errors.title.message}</p>}
            </div>
            <div>
              <label className="label">Job Type *</label>
              <select className="input" {...register('job_type')}>
                <option value="FULL_TIME">Full Time</option>
                <option value="INTERNSHIP">Internship</option>
                <option value="CONTRACT">Contract</option>
              </select>
              {errors.job_type && <p className="text-red-500 text-xs mt-1">{errors.job_type.message}</p>}
            </div>
          </div>

          <div>
            <label className="label">Job Description *</label>
            <textarea className="input min-h-[120px]" placeholder="Detailed description of the role..." {...register('description')} />
            {errors.description && <p className="text-red-500 text-xs mt-1">{errors.description.message}</p>}
          </div>
        </div>

        {/* Schedule */}
        <div className="card p-6 space-y-5">
          <h3 className="text-lg font-bold border-b border-gray-100 pb-2">Drive Schedule</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label className="label">Drive Date <span className="text-gray-400 font-normal ml-1">(Optional)</span></label>
              <input type="datetime-local" className="input" {...register('drive_date')} />
              {errors.drive_date && <p className="text-red-500 text-xs mt-1">{errors.drive_date.message}</p>}
            </div>
            <div>
              <label className="label">Reporting Time <span className="text-gray-400 font-normal ml-1">(Optional)</span></label>
              <input type="time" className="input" {...register('reporting_time')} />
              {errors.reporting_time && <p className="text-red-500 text-xs mt-1">{errors.reporting_time.message}</p>}
            </div>
          </div>
        </div>

        {/* Eligibility Criteria */}
        <div className="card p-6 space-y-5">
          <h3 className="text-lg font-bold border-b border-gray-100 pb-2">Eligibility Criteria</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label className="label">Minimum CGPA <span className="text-gray-400 font-normal ml-1">(0-10)</span></label>
              <input type="number" step="0.01" className="input" placeholder="e.g. 7.5" {...register('min_cgpa')} />
              {errors.min_cgpa && <p className="text-red-500 text-xs mt-1">{errors.min_cgpa.message}</p>}
            </div>
            <div>
              <label className="label">Maximum Active Backlogs</label>
              <input type="number" className="input" placeholder="e.g. 0" {...register('max_backlogs')} />
              {errors.max_backlogs && <p className="text-red-500 text-xs mt-1">{errors.max_backlogs.message}</p>}
            </div>
          </div>

          <div>
            <label className="label">Allowed Branches <span className="text-gray-400 font-normal ml-1">(Comma separated)</span></label>
            <input type="text" className="input" placeholder="e.g. CSE, IT, ECE" {...register('allowed_branches')} />
            <p className="text-xs text-gray-500 mt-1">Leave blank to allow all branches.</p>
            {errors.allowed_branches && <p className="text-red-500 text-xs mt-1">{errors.allowed_branches.message}</p>}
          </div>
        </div>

        <div className="flex justify-end gap-4 pt-4">
          <Link to="/dashboard" className="btn-ghost">Cancel</Link>
          <button type="submit" className="btn-primary !px-8" disabled={isSubmitting}>
            {isSubmitting ? 'Saving Draft...' : 'Submit Drive for Approval'}
          </button>
        </div>
      </form>
    </div>
  );
}
