import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

api.interceptors.request.use((req) => {
  console.log('➡️ API Request:', req.method, req.url)
  return req
})

let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: unknown) => void
  reject: (reason?: unknown) => void
}> = []

const processQueue = (error: unknown = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve()
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.code === 'ERR_NETWORK') {
      window.location.href = '/network-issue'
      return Promise.reject(error)
    }
    const isRefreshRequest = originalRequest.url?.includes('/auth/refresh')

    if (
      error.response &&
      error.response.status === 401 &&
      window.location.pathname != '/login' &&
      !isRefreshRequest &&
      window.location.pathname != '/register' &&
      !originalRequest._retry
    ) {
      originalRequest._retry = true
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(() => api(originalRequest))
      }

      isRefreshing = true

      try {
        console.log('apiasdasm')
        await api.post('/auth/refresh')
        processQueue()
        return api(originalRequest)
      } catch (refreshError) {
        console.error('❌ Refresh failed. Logging out.')
        window.location.href = '/login'
        processQueue(refreshError)

        localStorage.clear()

        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)

export default api
