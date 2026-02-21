# Campus Placement Portal - Frontend

React + TypeScript frontend for the Campus Placement Portal system.

## Prerequisites

Before you can run the frontend, you need to have Node.js and npm installed:

### Installing Node.js

1. Download Node.js from [https://nodejs.org/](https://nodejs.org/)
   - **Recommended**: Download the LTS (Long Term Support) version
   - Current recommended version: Node.js 18.x or higher

2. Run the installer
   - Follow the installation wizard
   - Make sure to check the box that says "Automatically install necessary tools"
   - This will add Node.js and npm to your system PATH

3. Verify installation:
   ```powershell
   node --version
   npm --version
   ```

## Installation

Once Node.js is installed, install the project dependencies:

```powershell
cd "d:\Gourav\Project 1\Frontend"
npm install
```

This will install all required dependencies including:
- React 18
- TypeScript
- Vite (build tool)
- React Router (routing)
- Axios (HTTP client)
- TanStack Query (data fetching)
- Tailwind CSS (styling)
- Lucide React (icons)
- And more...

## Running the Development Server

Start the development server:

```powershell
npm run dev
```

The application will be available at: **http://localhost:3000**

The dev server includes:
- Hot Module Replacement (HMR) - instant updates as you code
- TypeScript type checking
- API proxy to backend (requests to `/api` are forwarded to `http://localhost:8000`)

## Project Structure

```
Frontend/
├── src/
│   ├── pages/              # Page components
│   │   ├── auth/          # Login, Register
│   │   ├── student/       # Student dashboard
│   │   ├── recruiter/     # Recruiter dashboard
│   │   ├── placement/     # Placement officer dashboard
│   │   ├── admin/         # Admin dashboard
│   │   ├── jobs/          # Job listings and details
│   │   ├── applications/  # Application management
│   │   ├── profile/       # User profile
│   │   ├── students/      # Student management
│   │   ├── recruiters/    # Recruiter management
│   │   └── errors/        # Error pages (404, 403)
│   ├── layouts/           # Layout components
│   │   ├── MainLayout.tsx # Main app layout with sidebar
│   │   └── AuthLayout.tsx # Login/register layout
│   ├── context/           # React Context providers
│   │   └── AuthContext.tsx # Authentication state management
│   ├── services/          # API services
│   │   └── api.ts        # API client and endpoints
│   ├── App.tsx           # Root component
│   ├── routes.tsx        # Route definitions
│   ├── main.tsx          # Application entry point
│   └── index.css         # Global styles with Tailwind
├── public/               # Static assets
├── index.html           # HTML template
├── package.json         # Dependencies and scripts
├── vite.config.ts       # Vite configuration
├── tsconfig.json        # TypeScript configuration
├── tailwind.config.js   # Tailwind CSS configuration
├── postcss.config.js    # PostCSS configuration
└── .env                 # Environment variables

```

## Environment Configuration

Create or edit `.env` file in the Frontend directory:

```env
# API Configuration
VITE_API_URL=http://localhost:8000/api
```

**Note**: Make sure the backend server is running on port 8000 before starting the frontend.

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Features Implemented

### Authentication
- ✅ Login page with email/password
- ✅ Register page (student/recruiter)
- ✅ JWT token-based authentication
- ✅ Protected routes with role-based access control
- ✅ Auto-redirect based on user role

### Layouts
- ✅ Main layout with sidebar navigation
- ✅ Auth layout for login/register
- ✅ Role-specific navigation items

### Dashboard Pages
- ✅ Student dashboard with job statistics
- ✅ Recruiter dashboard
- ✅ Placement officer dashboard
- ✅ Admin dashboard
- ✅ Generic dashboard for all users

### Pages (Placeholders)
- ✅ Jobs list and details
- ✅ Create job (for recruiters)
- ✅ My applications
- ✅ Application details
- ✅ Profile and edit profile
- ✅ Students management
- ✅ Recruiters management
- ✅ Error pages (404, 403)

### API Integration
- ✅ Axios client with interceptors
- ✅ Automatic token injection
- ✅ Auto-redirect on 401 (unauthorized)
- ✅ API endpoints for all resources:
  - Auth (login, register)
  - Students
  - Recruiters
  - Jobs
  - Applications
  - Resumes
  - Colleges
  - Users

## Testing the Application

### Demo Credentials

Use these credentials to test different user roles:

**Admin:**
- Email: `admin@collegex.edu`
- Password: `admin123`

**Placement Officer:**
- Email: `placement@collegex.edu`
- Password: `placement123`

### Quick Start Guide

1. Make sure the backend is running:
   ```powershell
   cd "d:\Gourav\Project 1\Backend"
   uvicorn app.main:app --reload
   ```
   Backend should be at: http://localhost:8000

2. Install frontend dependencies (if not already done):
   ```powershell
   cd "d:\Gourav\Project 1\Frontend"
   npm install
   ```

3. Start the frontend:
   ```powershell
   npm run dev
   ```
   Frontend should be at: http://localhost:3000

4. Open http://localhost:3000 in your browser

5. Login with admin credentials or create a new account

## Technology Stack

- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Next-generation build tool
- **React Router** - Client-side routing
- **TailwindCSS** - Utility-first CSS framework
- **Axios** - HTTP client
- **TanStack Query** - Data fetching and caching
- **Zustand** - State management (lightweight)
- **React Hook Form** - Form handling
- **Zod** - Schema validation
- **Lucide React** - Icon library
- **date-fns** - Date utilities

## Next Steps

The frontend structure is ready with:
- ✅ Authentication flow
- ✅ Protected routes
- ✅ Role-based dashboards
- ✅ API integration setup

### To Complete:

1. **Implement full pages** - The placeholder pages need to be fully implemented with:
   - Job listing with filters and search
   - Job details with apply functionality
   - Application tracking and status updates
   - Profile management forms
   - Student/Recruiter management tables
   - Admin controls

2. **Add form validation** - Use React Hook Form + Zod for all forms

3. **Improve UI/UX** - Add:
   - Loading states
   - Error handling
   - Success notifications
   - Better responsive design

4. **Add features**:
   - Resume upload
   - Job search and filters
   - Application status tracking
   - Email notifications
   - Export reports (for placement officers)

## Troubleshooting

### Port 3000 already in use
If port 3000 is already in use, you can change it in `vite.config.ts`:
```typescript
server: {
  port: 3001,  // Change to any available port
}
```

### Cannot connect to backend
- Make sure the backend is running on port 8000
- Check the `VITE_API_URL` in `.env` file
- Verify CORS is properly configured in the backend

### TypeScript errors
- Run `npm install` to ensure all types are installed
- Check `tsconfig.json` for proper configuration
- Restart VS Code if IntelliSense isn't working

## Support

For issues or questions:
1. Check the backend is running and accessible
2. Verify Node.js and npm are properly installed
3. Clear node_modules and reinstall: `rm -rf node_modules; npm install`
4. Check browser console for errors
