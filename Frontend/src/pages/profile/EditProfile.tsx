import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/context/AuthContext'
import { studentsApi, recruitersApi } from '@/services/api'
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Save, User, GraduationCap, Link as LinkIcon, Briefcase } from 'lucide-react'

type Tab = 'personal' | 'education' | 'links'

const INPUT = "w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"

export default function EditProfile() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<Tab>('personal')
  const [form, setForm] = useState<any>({})
  const [saveMsg, setSaveMsg] = useState('')
  const [error, setError] = useState('')

  const isRecruiter = user?.role === 'recruiter'

  const { data: profile, isLoading } = useQuery({
    queryKey: ['edit-profile', user?.id],
    queryFn: async () => {
      if (isRecruiter) {
        const res = await recruitersApi.getAll({ user_id: user?.id })
        const items = res.data
        return Array.isArray(items) ? items.find((r: any) => r.user_id === user?.id) : items
      } else {
        const res = await studentsApi.getAll({ user_id: user?.id })
        const items = res.data
        return Array.isArray(items) ? items.find((s: any) => s.user_id === user?.id) : items
      }
    },
    enabled: !!user?.id,
  })

  useEffect(() => {
    if (profile) setForm(profile)
  }, [profile])

  const f = (key: string) => form[key] ?? ''
  const set = (key: string) => (e: any) => setForm((prev: any) => ({ ...prev, [key]: e.target.value }))

  const updateMutation = useMutation({
    mutationFn: (data: any) => {
      if (isRecruiter) return recruitersApi.update(profile.id, data)
      return studentsApi.update(profile.id, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student-profile'] })
      queryClient.invalidateQueries({ queryKey: ['edit-profile'] })
      setSaveMsg('Changes saved!')
      setTimeout(() => { setSaveMsg(''); navigate('/profile') }, 1500)
    },
    onError: (err: any) => setError(err.response?.data?.detail || 'Save failed'),
  })

  const tabs: { id: Tab; label: string; icon: any }[] = [
    { id: 'personal', label: 'Personal', icon: User },
    { id: 'education', label: isRecruiter ? 'Company' : 'Education', icon: isRecruiter ? Briefcase : GraduationCap },
    { id: 'links', label: 'Links', icon: LinkIcon },
  ]

  if (isLoading) return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 bg-gray-200 rounded w-1/4" />
      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        {[1, 2, 3].map(i => <div key={i} className="h-10 bg-gray-100 rounded" />)}
      </div>
    </div>
  )

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate('/profile')} className="text-gray-500 hover:text-gray-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-2xl font-bold text-gray-900">Edit Profile</h1>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1 mb-6 w-fit">
        {tabs.map(tab => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === tab.id ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'
                }`}
            >
              <Icon className="w-4 h-4" /> {tab.label}
            </button>
          )
        })}
      </div>

      {error && <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{error}</div>}
      {saveMsg && <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm font-medium">✓ {saveMsg}</div>}

      <div className="bg-white rounded-lg shadow p-6">
        {/* Personal tab */}
        {activeTab === 'personal' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
              <input className={INPUT} value={f('first_name')} onChange={set('first_name')} placeholder="First name" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
              <input className={INPUT} value={f('last_name')} onChange={set('last_name')} placeholder="Last name" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input className={INPUT} value={f('phone')} onChange={set('phone')} placeholder="+91 XXXXX XXXXX" />
            </div>
            {!isRecruiter && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Enrollment Number</label>
                <input className={INPUT} value={f('enrollment_number')} onChange={set('enrollment_number')} placeholder="e.g. 2021CSE001" />
              </div>
            )}
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Bio</label>
              <textarea
                className={INPUT + " resize-none"}
                rows={4}
                value={f('bio')}
                onChange={set('bio')}
                placeholder="A short description about yourself..."
              />
            </div>
          </div>
        )}

        {/* Education / Company tab */}
        {activeTab === 'education' && !isRecruiter && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">University</label>
              <input className={INPUT} value={f('university')} onChange={set('university')} placeholder="e.g. IIT Delhi" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Degree</label>
              <input className={INPUT} value={f('degree')} onChange={set('degree')} placeholder="e.g. B.Tech" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Major</label>
              <input className={INPUT} value={f('major')} onChange={set('major')} placeholder="e.g. Computer Science" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Branch</label>
              <input className={INPUT} value={f('branch')} onChange={set('branch')} placeholder="e.g. CSE" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Graduation Year</label>
              <input className={INPUT} type="number" value={f('graduation_year')} onChange={set('graduation_year')} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">CGPA</label>
              <input className={INPUT} type="number" step="0.1" min="0" max="10" value={f('cgpa')} onChange={set('cgpa')} placeholder="e.g. 8.5" />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Skills <span className="text-gray-400 font-normal">(comma-separated)</span></label>
              <input className={INPUT} value={f('skills')} onChange={set('skills')} placeholder="e.g. Python, React, SQL" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Has Backlogs</label>
              <select className={INPUT} value={f('has_backlogs') ? 'true' : 'false'} onChange={e => setForm((p: any) => ({ ...p, has_backlogs: e.target.value === 'true' }))}>
                <option value="false">No</option>
                <option value="true">Yes</option>
              </select>
            </div>
          </div>
        )}

        {activeTab === 'education' && isRecruiter && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Company Name</label>
              <input className={INPUT} value={f('company_name')} onChange={set('company_name')} placeholder="e.g. Acme Corp" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Position / Title</label>
              <input className={INPUT} value={f('position')} onChange={set('position')} placeholder="e.g. HR Manager" />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Company Website</label>
              <input className={INPUT} value={f('company_website')} onChange={set('company_website')} placeholder="https://acme.com" />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Company Description</label>
              <textarea className={INPUT + " resize-none"} rows={4} value={f('company_description')} onChange={set('company_description')} />
            </div>
          </div>
        )}

        {/* Links tab */}
        {activeTab === 'links' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">🔗 LinkedIn URL</label>
              <input className={INPUT} value={f('linkedin_url')} onChange={set('linkedin_url')} placeholder="https://linkedin.com/in/..." />
            </div>
            {!isRecruiter && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">🐙 GitHub URL</label>
                  <input className={INPUT} value={f('github_url')} onChange={set('github_url')} placeholder="https://github.com/..." />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">🌐 Portfolio / Website</label>
                  <input className={INPUT} value={f('portfolio_url')} onChange={set('portfolio_url')} placeholder="https://..." />
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3 mt-6">
        <button
          onClick={() => navigate('/profile')}
          className="px-5 py-2.5 border border-gray-300 text-gray-600 text-sm font-medium rounded-lg hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={() => updateMutation.mutate(form)}
          disabled={updateMutation.isPending}
          className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-60 transition-colors"
        >
          <Save className="w-4 h-4" />
          {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  )
}
