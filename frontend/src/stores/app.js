import { defineStore } from 'pinia'

const defaultCoverage = { Java基础: 'pending', 'Spring Boot': 'pending', MySQL: 'pending', Redis: 'pending', 分布式: 'pending' }

export const useAppStore = defineStore('app', {
  state: () => ({
    resumeReady: false,
    selectedJob: 'Java开发工程师',
    jobCompetencies: [],
    competencyModel: [],
    jobKnowledgeReady: false,
    candidate: {
      name: '张三', education: '本科', major: '计算机科学与技术', direction: 'Java开发工程师',
      skills: ['Java', 'Spring Boot', 'MySQL', 'Redis', 'Docker'],
      projects: [{ name: '智能招聘系统', technology: 'Spring Boot、MySQL、Redis', responsibility: '负责后端接口设计和数据库优化。', result: '完成核心招聘流程上线。' }],
      strength: '工程实践能力较强。', weakness: '分布式系统经验不足。', potentialQuestions: [], analysisMode: 'fallback', warning: null,
    },
    interview: { sessionId: null, job: '', stage: '基础能力', progress: 0, total: 10, ability: '岗位能力', abilityCoverage: { ...defaultCoverage }, messages: [], completed: false, agentTrace: [], evidences: [], ragEnhanced: false, agentMode: 'fallback', projectContext: {}, technicalPoints: [] },
  }),
  actions: {
    markResumeReady() { this.resumeReady = true },
    setJobCompetencies(data) {
      this.jobCompetencies = data.competencies || []
      this.jobKnowledgeReady = Boolean(data.ready)
    },
    setCompetencyModel(data) { this.competencyModel = data.competencies || [] },
    setCandidate(profile) {
      this.candidate = {
        name: profile.name,
        education: profile.education,
        major: profile.major,
        direction: profile.target_job === '未知' ? this.selectedJob : profile.target_job,
        skills: profile.skills || [],
        projects: profile.projects || [],
        strength: profile.advantages?.join('；') || '待面试进一步评估',
        weakness: profile.weaknesses?.join('；') || '待面试进一步评估',
        potentialQuestions: profile.potential_questions || [],
        analysisMode: profile.analysis_mode,
        warning: profile.warning,
      }
      if (profile.target_job && profile.target_job !== '未知') this.selectedJob = profile.target_job
      this.resumeReady = true
    },
    initializeInterview(data) {
      this.interview = {
        sessionId: data.session_id, job: data.job, stage: data.stage, progress: data.progress, total: data.total,
        ability: data.ability, abilityCoverage: data.ability_coverage || { ...defaultCoverage }, completed: false,
        agentTrace: data.agent_trace || [], evidences: data.evidences || [], ragEnhanced: data.rag_enhanced, agentMode: data.agent_mode || 'fallback',
        projectContext: data.current_project_context || {}, technicalPoints: data.technical_points || [],
        messages: [
          { role: 'ai', text: `你好，${this.candidate.name}。我是本次${data.job}岗位的AI面试官。接下来我会结合你的回答进行动态追问。` },
          { role: 'ai', text: data.question, tag: data.ability },
        ],
      }
    },
    addInterviewMessage(message) { this.interview.messages.push(message) },
    updateInterview(data) {
      Object.assign(this.interview, { stage: data.stage, progress: data.progress, total: data.total, ability: data.analysis?.ability_detected || data.ability, abilityCoverage: data.ability_coverage, completed: data.completed, agentTrace: data.agent_trace || [], evidences: data.evidences || [], ragEnhanced: data.rag_enhanced, agentMode: data.agent_mode || 'fallback', projectContext: data.current_project_context || {}, technicalPoints: data.technical_points || data.analysis?.technical_points || [] })
    },
    resetInterview() {
      Object.assign(this.interview, { sessionId: null, messages: [], progress: 0, completed: false, abilityCoverage: { ...defaultCoverage }, agentTrace: [], evidences: [], ragEnhanced: false, projectContext: {}, technicalPoints: [] })
    },
  },
})
