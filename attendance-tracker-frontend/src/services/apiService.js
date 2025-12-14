import axios from 'axios'

const API_BASE_URL = '/api'

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
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

export const apiService = {
  // Subjects
  async getSubjects() {
    const response = await api.get('/subjects')
    return response.data
  },

  async createSubject(subjectData) {
    const response = await api.post('/subjects', subjectData)
    return response.data
  },

  async updateSubject(id, subjectData) {
    const response = await api.put(`/subjects/${id}`, subjectData)
    return response.data
  },

  async deleteSubject(id) {
    const response = await api.delete(`/subjects/${id}`)
    return response.data
  },

  // Attendance
  async getAttendance(filters = {}) {
    const params = new URLSearchParams(filters)
    const response = await api.get(`/attendance?${params}`)
    return response.data
  },

  async markAttendance(attendanceData) {
    const response = await api.post('/attendance', attendanceData)
    return response.data
  },

  async updateAttendance(id, attendanceData) {
    const response = await api.put(`/attendance/${id}`, attendanceData)
    return response.data
  },

  async deleteAttendance(id) {
    const response = await api.delete(`/attendance/${id}`)
    return response.data
  },

  async getAttendanceStats() {
    const response = await api.get('/attendance/stats')
    return response.data
  },

  async getAttendanceTrends(period = 'week') {
    const response = await api.get(`/attendance/trends?period=${period}`)
    return response.data
  },

  async exportAttendance(format = 'pdf', filters = {}) {
    const params = new URLSearchParams({ format, ...filters })
    const response = await api.get(`/attendance/export?${params}`, {
      responseType: 'blob'
    })
    return response
  },

  // Tasks
  async getTasks(filters = {}) {
    const params = new URLSearchParams(filters)
    const response = await api.get(`/tasks?${params}`)
    return response.data
  },

  async createTask(taskData) {
    const response = await api.post('/tasks', taskData)
    return response.data
  },

  async updateTask(id, taskData) {
    const response = await api.put(`/tasks/${id}`, taskData)
    return response.data
  },

  async deleteTask(id) {
    const response = await api.delete(`/tasks/${id}`)
    return response.data
  },

  async getTaskStats() {
    const response = await api.get('/tasks/stats')
    return response.data
  },

  // Reminders
  async getReminders() {
    const response = await api.get('/reminders')
    return response.data
  },

  async createReminder(reminderData) {
    const response = await api.post('/reminders', reminderData)
    return response.data
  },

  async updateReminder(id, reminderData) {
    const response = await api.put(`/reminders/${id}`, reminderData)
    return response.data
  },

  async deleteReminder(id) {
    const response = await api.delete(`/reminders/${id}`)
    return response.data
  },

  async markReminderAsRead(id) {
    const response = await api.patch(`/reminders/${id}/read`)
    return response.data
  },

  // Analytics
  async getDashboardData() {
    const response = await api.get('/analytics/dashboard')
    return response.data
  },

  async getAttendanceAnalytics(period = 'month') {
    const response = await api.get(`/analytics/attendance?period=${period}`)
    return response.data
  },

  async getTaskAnalytics(period = 'month') {
    const response = await api.get(`/analytics/tasks?period=${period}`)
    return response.data
  },

  async getProductivityInsights() {
    const response = await api.get('/analytics/insights')
    return response.data
  }
}