import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '@/services/api'

interface User {
  id: number
  email: string
  role: string
  is_active: boolean
  college_id: number
}

interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, role: string, firstName: string, lastName: string, companyName?: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    // Check for stored token on mount
    const storedToken = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')

    if (storedToken && storedUser) {
      setToken(storedToken)
      setUser(JSON.parse(storedUser))
    }
    setLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    try {
      // Step 1: Login → get JWT tokens
      const response = await authApi.login(email, password)
      const { access_token } = response.data

      // Step 2: Store token first so getCurrentUser request is authenticated
      localStorage.setItem('token', access_token)
      setToken(access_token)

      // Step 3: Fetch the actual user data using the token
      const userResponse = await authApi.getCurrentUser()
      const userData = userResponse.data

      setUser(userData)
      localStorage.setItem('user', JSON.stringify(userData))

      // Navigate based on role
      switch (userData.role) {
        case 'admin':
          navigate('/admin')
          break
        case 'placement_officer':
          navigate('/placement')
          break
        case 'student':
          navigate('/student')
          break
        case 'recruiter':
          navigate('/recruiter')
          break
        default:
          navigate('/dashboard')
      }
    } catch (error) {
      // Clean up if login fails
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      setToken(null)
      setUser(null)
      console.error('Login failed:', error)
      throw error
    }
  }

  const register = async (email: string, password: string, role: string, firstName: string, lastName: string, companyName?: string) => {
    try {
      // Call the correct endpoint based on role
      if (role === 'student') {
        await authApi.registerStudent(email, password, {
          first_name: firstName,
          last_name: lastName,
          enrollment_number: null,
          graduation_year: new Date().getFullYear() + 1,
          cgpa: 0,
        })
      } else if (role === 'recruiter') {
        await authApi.registerRecruiter(email, password, {
          first_name: firstName,
          last_name: lastName,
          company_name: companyName || 'My Company',
          position: '',
          phone: '',
        })
      }

      // After registration, log in automatically
      await login(email, password)
    } catch (error) {
      console.error('Registration failed:', error)
      throw error
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        login,
        register,
        logout,
        loading,
      }}
    >
      {!loading && children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
