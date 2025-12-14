import axios from 'axios'

const API_URL = '/api/auth'

// Create axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add token to requests
api.interceptors.request.use(
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
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authService = {
  async login(email, password) {
    try {
      const response = await api.post('/login', { email, password })
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Login failed')
    }
  },

  async register(email, password, fullName) {
    try {
      const response = await api.post('/register', { 
        email, 
        password, 
        name: fullName 
      })
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Registration failed')
    }
  },

  async getCurrentUser() {
    try {
      const response = await api.get('/profile')
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to get user data')
    }
  },

  async updateProfile(profileData) {
    try {
      const response = await api.put('/profile', profileData)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Profile update failed')
    }
  }
}