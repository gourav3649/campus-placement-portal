import { Link } from 'react-router-dom'
import { Home, ShieldAlert } from 'lucide-react'

export default function Unauthorized() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="text-center">
        <ShieldAlert className="w-16 h-16 text-red-400 mx-auto mb-4" />
        <h1 className="text-6xl font-bold text-gray-900 mb-2">403</h1>
        <p className="text-xl text-gray-600 mb-2">Unauthorized Access</p>
        <p className="text-gray-500 mb-8">
          You don't have permission to access this page.
        </p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
        >
          <Home className="w-4 h-4" />
          Go back home
        </Link>
      </div>
    </div>
  )
}
