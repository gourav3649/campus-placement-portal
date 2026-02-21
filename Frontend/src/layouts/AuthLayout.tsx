import { Outlet } from 'react-router-dom'

export default function AuthLayout() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Campus Placement Portal
          </h1>
          <p className="mt-2 text-gray-600">College X</p>
        </div>
        <Outlet />
      </div>
    </div>
  )
}
