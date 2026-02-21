import { useAuth } from '@/context/AuthContext'

export default function Dashboard() {
  const { user } = useAuth()

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">Welcome, {user?.email}!</p>
        <p className="mt-2 text-sm text-gray-500">
          Role: <span className="font-medium">{user?.role}</span>
        </p>
      </div>
    </div>
  )
}
