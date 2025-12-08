import axios from 'axios'

const api = axios.create({
  baseURL: `/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})
export const setAuthToken = (token: string | null) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common['Authorization']
  }
}

api.interceptors.request.use((request) => {
  console.log('Starting Request', request.url, request.method, request.data)
  return request
})
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // console.log("axios error",error)
    if (error.code === 'ERR_NETWORK') {
      const currentPath = window.location.pathname + window.location.search
      if (window.location.pathname !== '/network-issue') {
        sessionStorage.setItem('previous_path', currentPath)
        window.location.href = '/network-issue'
      }
    }
    // console.log("window.location.pathname",window.location.pathname)
    if (
      error.response &&
      error.response.status === 401 &&
      window.location.pathname != '/login' &&
      window.location.pathname != '/register'
    ) {
      localStorage.clear()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)
export default api
