import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Handle response errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  // Login using JSON body (not OAuth2 form)
  login: (email: string, password: string) =>
    apiClient.post('/auth/login/json', { email, password }),

  // Register student — backend needs two separate objects
  registerStudent: (email: string, password: string, studentProfile: Record<string, any>) =>
    apiClient.post('/auth/register/student', {
      user_data: { email, password, role: 'student' },
      student_data: { ...studentProfile, user_id: 0 },
    }),

  // Register recruiter — backend needs two separate objects
  registerRecruiter: (email: string, password: string, recruiterProfile: Record<string, any>) =>
    apiClient.post('/auth/register/recruiter', {
      user_data: { email, password, role: 'recruiter' },
      recruiter_data: { ...recruiterProfile, user_id: 0 },
    }),

  getCurrentUser: () =>
    apiClient.get('/users/me'),
}

// Students API
export const studentsApi = {
  getAll: (params?: any) =>
    apiClient.get('/students', { params }),

  getById: (id: number) =>
    apiClient.get(`/students/${id}`),

  create: (data: any) =>
    apiClient.post('/students', data),

  update: (id: number, data: any) =>
    apiClient.put(`/students/${id}`, data),

  delete: (id: number) =>
    apiClient.delete(`/students/${id}`),
}

// Recruiters API
export const recruitersApi = {
  getAll: (params?: any) =>
    apiClient.get('/recruiters', { params }),

  getById: (id: number) =>
    apiClient.get(`/recruiters/${id}`),

  create: (data: any) =>
    apiClient.post('/recruiters', data),

  update: (id: number, data: any) =>
    apiClient.put(`/recruiters/${id}`, data),

  delete: (id: number) =>
    apiClient.delete(`/recruiters/${id}`),
}

// Jobs API
export const jobsApi = {
  getAll: (params?: any) =>
    apiClient.get('/jobs', { params }),

  getById: (id: number) =>
    apiClient.get(`/jobs/${id}`),

  create: (data: any) =>
    apiClient.post('/jobs', data),

  update: (id: number, data: any) =>
    apiClient.put(`/jobs/${id}`, data),

  delete: (id: number) =>
    apiClient.delete(`/jobs/${id}`),
}

// Applications API
export const applicationsApi = {
  getAll: (params?: any) =>
    apiClient.get('/applications', { params }),

  getById: (id: number) =>
    apiClient.get(`/applications/${id}`),

  create: (data: any) =>
    apiClient.post('/applications', data),

  update: (id: number, data: any) =>
    apiClient.put(`/applications/${id}`, data),

  delete: (id: number) =>
    apiClient.delete(`/applications/${id}`),

  getMyApplications: () =>
    apiClient.get('/applications/my'),
}

// Resumes API
export const resumesApi = {
  upload: (studentId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post(`/resumes/${studentId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  download: (studentId: number) =>
    apiClient.get(`/resumes/${studentId}`, {
      responseType: 'blob',
    }),

  delete: (studentId: number) =>
    apiClient.delete(`/resumes/${studentId}`),
}

// Colleges API
export const collegesApi = {
  getAll: () =>
    apiClient.get('/colleges'),

  getById: (id: number) =>
    apiClient.get(`/colleges/${id}`),
}

// Users API
export const usersApi = {
  getAll: (params?: any) =>
    apiClient.get('/users', { params }),

  getById: (id: number) =>
    apiClient.get(`/users/${id}`),

  update: (id: number, data: any) =>
    apiClient.put(`/users/${id}`, data),

  delete: (id: number) =>
    apiClient.delete(`/users/${id}`),
}

export default apiClient
