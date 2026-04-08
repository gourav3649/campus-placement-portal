import { Outlet } from 'react-router-dom';

export default function AuthLayout() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-600 shadow-lg text-white font-bold text-2xl mb-4">
            C
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-gray-900">
            Campus Portal
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Sign in to start managing your placement journey.
          </p>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-8 px-4 shadow-xl shadow-gray-200/50 sm:rounded-2xl sm:px-10 border border-gray-100">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}
