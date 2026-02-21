import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { jobsApi } from '@/services/api'
import { ArrowLeft, Briefcase } from 'lucide-react'

const FIELD = ({ label, required = false, children }: any) => (
    <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
            {label} {required && <span className="text-red-500">*</span>}
        </label>
        {children}
    </div>
)

const INPUT_CLS = "w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
const TEXTAREA_CLS = INPUT_CLS + " resize-none"

export default function PostJob() {
    const navigate = useNavigate()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [form, setForm] = useState({
        title: '',
        company_name: '',
        location: '',
        job_type: 'full_time',
        description: '',
        requirements: '',
        responsibilities: '',
        required_skills: '',
        salary_min: '',
        salary_max: '',
        experience_years: '0',
        education_level: '',
        min_cgpa: '',
        allowed_branches: '',
        application_deadline: '',
        is_active: true,
    })

    const set = (key: string) => (e: any) => setForm(f => ({ ...f, [key]: e.target.value }))

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        try {
            const payload = {
                ...form,
                salary_min: form.salary_min ? Number(form.salary_min) : undefined,
                salary_max: form.salary_max ? Number(form.salary_max) : undefined,
                experience_years: form.experience_years ? Number(form.experience_years) : 0,
                min_cgpa: form.min_cgpa ? Number(form.min_cgpa) : undefined,
            }
            await jobsApi.create(payload)
            navigate('/recruiter', { state: { success: 'Job posted successfully!' } })
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to post job. Please try again.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div>
            <button onClick={() => navigate('/recruiter')} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6">
                <ArrowLeft className="w-4 h-4" /> Back to Dashboard
            </button>

            <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-blue-100 rounded-lg">
                    <Briefcase className="w-6 h-6 text-blue-600" />
                </div>
                <h1 className="text-2xl font-bold text-gray-900">Post a New Job</h1>
            </div>

            {error && (
                <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{error}</div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Basic Info */}
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="font-semibold text-gray-900 mb-4">Basic Information</h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <FIELD label="Job Title" required>
                            <input className={INPUT_CLS} value={form.title} onChange={set('title')} placeholder="e.g. Software Engineer" required />
                        </FIELD>
                        <FIELD label="Company Name" required>
                            <input className={INPUT_CLS} value={form.company_name} onChange={set('company_name')} placeholder="e.g. Acme Corp" required />
                        </FIELD>
                        <FIELD label="Location">
                            <input className={INPUT_CLS} value={form.location} onChange={set('location')} placeholder="e.g. Bangalore, India" />
                        </FIELD>
                        <FIELD label="Job Type" required>
                            <select className={INPUT_CLS} value={form.job_type} onChange={set('job_type')}>
                                <option value="full_time">Full Time</option>
                                <option value="part_time">Part Time</option>
                                <option value="internship">Internship</option>
                                <option value="contract">Contract</option>
                            </select>
                        </FIELD>
                    </div>
                </div>

                {/* Description */}
                <div className="bg-white rounded-lg shadow p-6 space-y-4">
                    <h2 className="font-semibold text-gray-900">Details</h2>
                    <FIELD label="Job Description" required>
                        <textarea className={TEXTAREA_CLS} rows={5} value={form.description} onChange={set('description')} placeholder="Describe the role..." required />
                    </FIELD>
                    <FIELD label="Requirements">
                        <textarea className={TEXTAREA_CLS} rows={4} value={form.requirements} onChange={set('requirements')} placeholder="List key requirements..." />
                    </FIELD>
                    <FIELD label="Responsibilities">
                        <textarea className={TEXTAREA_CLS} rows={4} value={form.responsibilities} onChange={set('responsibilities')} placeholder="List key responsibilities..." />
                    </FIELD>
                    <FIELD label="Required Skills">
                        <input className={INPUT_CLS} value={form.required_skills} onChange={set('required_skills')} placeholder="e.g. Python, React, SQL (comma-separated)" />
                    </FIELD>
                </div>

                {/* Compensation & Eligibility */}
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="font-semibold text-gray-900 mb-4">Compensation & Eligibility</h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <FIELD label="Min Salary (LPA)">
                            <input className={INPUT_CLS} type="number" min="0" value={form.salary_min} onChange={set('salary_min')} placeholder="e.g. 8" />
                        </FIELD>
                        <FIELD label="Max Salary (LPA)">
                            <input className={INPUT_CLS} type="number" min="0" value={form.salary_max} onChange={set('salary_max')} placeholder="e.g. 15" />
                        </FIELD>
                        <FIELD label="Min Experience (years)">
                            <input className={INPUT_CLS} type="number" min="0" value={form.experience_years} onChange={set('experience_years')} placeholder="0" />
                        </FIELD>
                        <FIELD label="Education Level">
                            <input className={INPUT_CLS} value={form.education_level} onChange={set('education_level')} placeholder="e.g. B.Tech, M.Tech" />
                        </FIELD>
                        <FIELD label="Min CGPA">
                            <input className={INPUT_CLS} type="number" step="0.1" min="0" max="10" value={form.min_cgpa} onChange={set('min_cgpa')} placeholder="e.g. 7.0" />
                        </FIELD>
                        <FIELD label="Allowed Branches">
                            <input className={INPUT_CLS} value={form.allowed_branches} onChange={set('allowed_branches')} placeholder="e.g. CSE, IT, ECE" />
                        </FIELD>
                        <FIELD label="Application Deadline">
                            <input className={INPUT_CLS} type="date" value={form.application_deadline} onChange={set('application_deadline')} />
                        </FIELD>
                    </div>
                </div>

                <div className="flex gap-3 justify-end">
                    <button
                        type="button"
                        onClick={() => navigate('/recruiter')}
                        className="px-5 py-2.5 border border-gray-300 text-gray-600 text-sm font-medium rounded-lg hover:bg-gray-50"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={loading}
                        className="px-6 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-60 transition-colors"
                    >
                        {loading ? 'Posting...' : 'Post Job'}
                    </button>
                </div>
            </form>
        </div>
    )
}
