import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../../services/api';
import { Loader2 } from 'lucide-react';
import { College } from '../../types';

const regSchema = z.object({
  email: z.string().email('Valid email required'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  college_id: z.number().min(1, 'Please select your college'),
  name: z.string().min(2, 'Full name is required'),
  role: z.enum(['STUDENT', 'RECRUITER']),
  
  // Student specific
  roll_number: z.string().optional(),
  branch: z.string().optional(),
  cgpa: z.number().min(0).max(10).optional(),
  has_backlogs: z.boolean().optional(),
  
  // Recruiter specific
  company_name: z.string().optional(),
  designation: z.string().optional(),
}).superRefine((data, ctx) => {
  if (data.role === 'STUDENT') {
    if (!data.roll_number) ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Required for students', path: ['roll_number'] });
    if (!data.branch) ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Required', path: ['branch'] });
    if (data.cgpa === undefined) ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Required', path: ['cgpa'] });
  }
  if (data.role === 'RECRUITER') {
    if (!data.company_name) ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Required for recruiters', path: ['company_name'] });
    if (!data.designation) ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Required', path: ['designation'] });
  }
});

type RegForm = z.infer<typeof regSchema>;

export default function Register() {
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [colleges, setColleges] = useState<College[]>([]);
  const navigate = useNavigate();

  const { register, handleSubmit, watch, formState: { errors } } = useForm<RegForm>({
    resolver: zodResolver(regSchema),
    defaultValues: { role: 'STUDENT', has_backlogs: false }
  });

  const selectedRole = watch('role');

  useEffect(() => {
    api.get<College[]>('/colleges').then(res => setColleges(res.data)).catch(console.error);
  }, []);

  const onSubmit = async (data: RegForm) => {
    try {
      setIsLoading(true); setError(''); setSuccess('');
      
      const payload: any = {
        email: data.email,
        password: data.password,
        college_id: data.college_id,
        name: data.name
      };
      
      if (data.role === 'STUDENT') {
        payload.roll_number = data.roll_number;
        payload.branch = data.branch;
        payload.cgpa = data.cgpa;
        payload.has_backlogs = data.has_backlogs;
        payload.graduation_year = new Date().getFullYear() + 1; // default assumption for now
      } else {
        payload.company_name = data.company_name;
        payload.designation = data.designation;
      }

      await api.post(`/auth/register/${data.role.toLowerCase()}`, payload);
      setSuccess('Registration successful! Redirecting to login...');
      setTimeout(() => navigate('/login'), 2000);
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full">
      <h3 className="text-xl font-semibold mb-6 text-gray-900">Create an Account</h3>
      
      {error && <div className="mb-4 p-3 rounded-xl bg-red-50 text-red-600 text-sm border border-red-100">{error}</div>}
      {success && <div className="mb-4 p-3 rounded-xl bg-green-50 text-green-700 text-sm border border-green-100">{success}</div>}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <label className={`cursor-pointer border rounded-xl px-4 py-3 text-center text-sm font-medium transition-colors ${selectedRole === 'STUDENT' ? 'bg-blue-50 border-blue-500 text-blue-700' : 'border-gray-200 text-gray-600 hover:bg-gray-50'}`}>
            <input type="radio" value="STUDENT" {...register('role')} className="hidden" />
            Student
          </label>
          <label className={`cursor-pointer border rounded-xl px-4 py-3 text-center text-sm font-medium transition-colors ${selectedRole === 'RECRUITER' ? 'bg-blue-50 border-blue-500 text-blue-700' : 'border-gray-200 text-gray-600 hover:bg-gray-50'}`}>
            <input type="radio" value="RECRUITER" {...register('role')} className="hidden" />
            Recruiter
          </label>
        </div>

        <div>
          <label className="label">College</label>
          <select {...register('college_id', { valueAsNumber: true })} className={`input ${errors.college_id ? 'input-error' : ''}`}>
            <option value={0}>Select your college...</option>
            {colleges.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          {errors.college_id && <p className="mt-1 text-xs text-red-600">{errors.college_id.message}</p>}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Full Name</label>
            <input {...register('name')} className={`input ${errors.name ? 'input-error' : ''}`} />
            {errors.name && <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>}
          </div>
          <div>
            <label className="label">Email address</label>
            <input type="email" {...register('email')} className={`input ${errors.email ? 'input-error' : ''}`} />
            {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
          </div>
        </div>

        <div>
          <label className="label">Password</label>
          <input type="password" {...register('password')} className={`input ${errors.password ? 'input-error' : ''}`} />
          {errors.password && <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>}
        </div>

        {selectedRole === 'STUDENT' && (
          <div className="grid grid-cols-2 gap-4 p-4 mt-2 bg-blue-50/50 rounded-xl border border-blue-100">
            <div>
              <label className="label text-blue-900">Roll Number</label>
              <input {...register('roll_number')} className="input" />
              {errors.roll_number && <p className="mt-1 text-xs text-red-600">{errors.roll_number.message}</p>}
            </div>
            <div>
              <label className="label text-blue-900">Branch (e.g. CSE)</label>
              <input {...register('branch')} className="input" />
              {errors.branch && <p className="mt-1 text-xs text-red-600">{errors.branch.message}</p>}
            </div>
            <div>
              <label className="label text-blue-900">Current CGPA</label>
              <input type="number" step="0.01" {...register('cgpa', { valueAsNumber: true })} className="input" />
              {errors.cgpa && <p className="mt-1 text-xs text-red-600">{errors.cgpa.message}</p>}
            </div>
            <div className="flex items-end pb-2">
              <label className="flex items-center gap-2 cursor-pointer text-sm font-medium text-blue-900">
                <input type="checkbox" {...register('has_backlogs')} className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-600" />
                Active backlogs?
              </label>
            </div>
          </div>
        )}

        {selectedRole === 'RECRUITER' && (
          <div className="grid grid-cols-2 gap-4 p-4 mt-2 bg-blue-50/50 rounded-xl border border-blue-100">
            <div>
              <label className="label text-blue-900">Company Name</label>
              <input {...register('company_name')} className="input" />
              {errors.company_name && <p className="mt-1 text-xs text-red-600">{errors.company_name.message}</p>}
            </div>
            <div>
              <label className="label text-blue-900">Designation</label>
              <input {...register('designation')} className="input" />
              {errors.designation && <p className="mt-1 text-xs text-red-600">{errors.designation.message}</p>}
            </div>
          </div>
        )}

        <button type="submit" disabled={isLoading} className="btn-primary w-full justify-center !py-2.5 mt-4">
          {isLoading ? <Loader2 className="animate-spin" size={18} /> : 'Create Account'}
        </button>
      </form>

      <div className="mt-6 text-center text-sm text-gray-600">
        Already have an account?{' '}
        <Link to="/login" className="font-semibold text-blue-600 hover:text-blue-500 hover:underline">Sign in</Link>
      </div>
    </div>
  );
}
