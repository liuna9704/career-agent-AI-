import axios from 'axios'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
})

http.interceptors.response.use(
  response => response.data,
  error => Promise.reject(new Error(error.response?.data?.detail || '服务暂时不可用，请稍后重试')),
)

export default http

