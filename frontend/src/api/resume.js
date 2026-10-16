import http from './http'

export const uploadResume = (file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)
  return http.post('/resume/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: event => {
      if (event.total && onProgress) onProgress(Math.round((event.loaded * 70) / event.total))
    },
  })
}

export const loadDemoResume = job => http.post(`/resume/demo/${encodeURIComponent(job)}`)
