import http from './http'

export const getJobs = () => http.get('/jobs')
export const getJobCompetencies = job => http.get(`/jobs/${encodeURIComponent(job)}/competencies`)
export const getCompetencyModel = job => http.get(`/jobs/${encodeURIComponent(job)}/competency-model`)
export const searchKnowledge = data => http.post('/knowledge/search', data)
