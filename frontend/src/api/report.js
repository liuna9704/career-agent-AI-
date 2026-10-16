import http from './http'

export const getAssessmentReport = sessionId => http.get(`/report/${sessionId}`)

