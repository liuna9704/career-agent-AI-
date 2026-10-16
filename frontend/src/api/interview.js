import http from './http'

export const startInterview = job => http.post('/interview/start', { job })

export const sendInterviewMessage = data => http.post('/interview/chat', data)

