import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/context/AuthContext'
import { studentsApi } from '@/services/api'
import { useState } from 'react'
import { User, Phone, GraduationCap, Briefcase, Link as LinkIcon, Edit2, Save, X } from 'lucide-react'

export default function Profile() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState<any>({})
  const [saveMsg, setSaveMsg] = useState('')

  const { data: profile, isLoading } = useQuery({
    queryKey: ['student-profile', user?.id],
    queryFn: async () => {
      // Get student profile details
      const res = await studentsApi.getAll({ user_id: user?.id })
      const students = res.data
      const me = Array.isArray(students) ? students.find((s: any) => s.user_id === user?.id) : students
      if (me) setForm(me)
      return me
    },
    enabled: !!user?.id,
  })

  const updateMutation = useMutation({
    mutationFn: (data: any) => studentsApi.update(profile.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student-profile'] })
      setEditing(false)
      setSaveMsg('Profile updated successfully!')
      setTimeout(() => setSaveMsg(''), 3000)
    },
  })

  const Field = ({ label, icon: Icon, value, field, type = 'text' }: any) => (
    <div className="flex flex-col gap-1">
      <label className="flex items-center gap-1.5 text-xs font-medium text-gray-500 uppercase tracking-wide">
        <Icon className="w-3.5 h-3.5" /> {label}
      </label>
      {editing ? (
        <input
          type={type}
          value={form[field] ?? ''}
          onChange={e => setForm({ ...form, [field]: e.target.value })}
          className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      ) : (
        <p className="text-gray-900 text-sm">{value || <span className="text-gray-400 italic">Not set</span>}</p>
      )}
    </div>
  )

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>
        {!editing ? (
          <button
            onClick={() => { setForm(profile || {}); setEditing(true) }}
            className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Edit2 className="w-4 h-4" /> Edit Profile
          </button>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={() => setEditing(false)}
              className="flex items-center gap-1.5 px-3 py-2 border border-gray-300 text-gray-600 text-sm rounded-lg hover:bg-gray-50"
            >
              <X className="w-4 h-4" /> Cancel
            </button>
            <button
              onClick={() => updateMutation.mutate(form)}
              disabled={updateMutation.isPending}
              className="flex items-center gap-1.5 px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-60"
            >
              <Save className="w-4 h-4" /> {updateMutation.isPending ? 'Saving...' : 'Save'}
            </button>
          </div>
        )}
      </div>

      {saveMsg && (
        <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">
          {saveMsg}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column – account info */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <div className="w-20 h-20 bg-blue-100 rounded-full mx-auto flex items-center justify-center mb-3">
              <User className="w-10 h-10 text-blue-600" />
            </div>
            <p className="font-semibold text-gray-900">
              {profile ? `${profile.first_name} ${profile.last_name}` : user?.email}
            </p>
            <p className="text-sm text-gray-500 capitalize mt-0.5">{user?.role?.replace('_', ' ')}</p>
            <span className={`inline-block mt-2 px-2 py-0.5 text-xs rounded-full font-medium ${user?.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
              {user?.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>

          <div className="bg-white rounded-lg shadow p-6 space-y-3">
            <h3 className="font-semibold text-gray-900 text-sm">Account</h3>
            <div>
              <label className="text-xs text-gray-500 uppercase tracking-wide">Email</label>
              <p className="text-sm text-gray-900 mt-0.5">{user?.email}</p>
            </div>
          </div>
        </div>

        {/* Right columns – profile details */}
        <div className="lg:col-span-2 space-y-4">
          {isLoading ? (
            <div className="bg-white rounded-lg shadow p-6 animate-pulse space-y-4">
              {[1, 2, 3, 4].map(i => (
                <div key={i}>
                  <div className="h-3 bg-gray-200 rounded w-1/4 mb-1" />
                  <div className="h-5 bg-gray-100 rounded w-1/2" />
                </div>
              ))}
            </div>
          ) : (
            <>
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <User className="w-4 h-4 text-blue-600" /> Personal Info
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Field label="First Name" icon={User} value={profile?.first_name} field="first_name" />
                  <Field label="Last Name" icon={User} value={profile?.last_name} field="last_name" />
                  <Field label="Phone" icon={Phone} value={profile?.phone} field="phone" />
                  <Field label="Enrollment No." icon={Briefcase} value={profile?.enrollment_number} field="enrollment_number" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <GraduationCap className="w-4 h-4 text-blue-600" /> Education
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Field label="University" icon={GraduationCap} value={profile?.university} field="university" />
                  <Field label="Degree" icon={GraduationCap} value={profile?.degree} field="degree" />
                  <Field label="Major" icon={GraduationCap} value={profile?.major} field="major" />
                  <Field label="Branch" icon={GraduationCap} value={profile?.branch} field="branch" />
                  <Field label="Graduation Year" icon={GraduationCap} value={profile?.graduation_year} field="graduation_year" type="number" />
                  <Field label="CGPA" icon={GraduationCap} value={profile?.cgpa} field="cgpa" type="number" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <LinkIcon className="w-4 h-4 text-blue-600" /> Links & Bio
                </h3>
                <div className="space-y-4">
                  <Field label="LinkedIn" icon={LinkIcon} value={profile?.linkedin_url} field="linkedin_url" />
                  <Field label="GitHub" icon={LinkIcon} value={profile?.github_url} field="github_url" />
                  <Field label="Portfolio" icon={LinkIcon} value={profile?.portfolio_url} field="portfolio_url" />
                  {editing ? (
                    <div>
                      <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Bio</label>
                      <textarea
                        value={form.bio ?? ''}
                        onChange={e => setForm({ ...form, bio: e.target.value })}
                        rows={3}
                        className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  ) : (
                    <div>
                      <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Bio</label>
                      <p className="text-sm text-gray-900 mt-0.5">{profile?.bio || <span className="text-gray-400 italic">Not set</span>}</p>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
