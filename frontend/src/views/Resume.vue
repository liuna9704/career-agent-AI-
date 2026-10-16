<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import PageHeading from '../components/PageHeading.vue'
import { useAppStore } from '../stores/app'
import { loadDemoResume, uploadResume } from '../api/resume'
import { getCompetencyModel, getJobCompetencies } from '../api/jobs'

const router = useRouter()
const store = useAppStore()
const fileName = ref(store.resumeReady ? '候选人简历.pdf' : '')
const progress = ref(store.resumeReady ? 100 : 0)
const status = ref(store.resumeReady ? 'done' : 'idle')
const analysisStep = ref(store.resumeReady ? 4 : 0)
const steps = ['上传文件', '文本提取', 'AI分析中', '生成画像']
const avatarText = computed(() => store.candidate.name?.slice(0, 1) || '候')
const jobLoading = ref(false)

const loadCompetencies = async job => {
  jobLoading.value = true
  try {
    const [knowledgeResponse, modelResponse] = await Promise.all([getJobCompetencies(job), getCompetencyModel(job)])
    store.setJobCompetencies(knowledgeResponse.data)
    store.setCompetencyModel(modelResponse.data)
  } catch (error) {
    store.setJobCompetencies({ competencies: [], ready: false })
    store.setCompetencyModel({ competencies: [] })
    ElMessage.error(error.message)
  } finally {
    jobLoading.value = false
  }
}

watch(() => store.selectedJob, loadCompetencies, { immediate: true })

const beforeUpload = async (file) => {
  const extension = file.name.split('.').pop()?.toLowerCase()
  if (!['pdf', 'docx'].includes(extension)) { ElMessage.error('仅支持 PDF 或 DOCX 格式'); return false }
  if (file.size > 10 * 1024 * 1024) { ElMessage.error('简历文件不能超过 10MB'); return false }

  fileName.value = file.name
  progress.value = 5
  status.value = 'parsing'
  analysisStep.value = 1
  const stageTimer = window.setTimeout(() => { if (status.value === 'parsing') analysisStep.value = 3 }, 900)
  try {
    const response = await uploadResume(file, value => {
      progress.value = Math.max(progress.value, value)
      if (value >= 60) analysisStep.value = 2
    })
    progress.value = 92
    analysisStep.value = 4
    store.setCandidate(response.data)
    window.setTimeout(() => { progress.value = 100; status.value = 'done' }, 250)
    if (response.data.analysis_mode === 'fallback') ElMessage.warning(response.data.warning || response.message)
    else ElMessage.success(response.message)
  } catch (error) {
    progress.value = 0
    status.value = 'idle'
    analysisStep.value = 0
    ElMessage.error(error.message)
  } finally {
    window.clearTimeout(stageTimer)
  }
  return false
}

const startInterview = () => router.push('/interview')
const loadDemo = async () => {
  status.value = 'parsing'; analysisStep.value = 3; progress.value = 72; fileName.value = `${store.selectedJob}_演示简历.pdf`
  try {
    const response = await loadDemoResume(store.selectedJob)
    store.setCandidate(response.data); analysisStep.value = 4; progress.value = 100; status.value = 'done'
    ElMessage.success('一键演示数据加载完成')
  } catch (error) { status.value = 'idle'; ElMessage.error(error.message) }
}
</script>

<template>
  <main class="page resume-page">
    <PageHeading eyebrow="Resume Intelligence" title="简历智能分析" description="真实提取PDF或Word文本，并通过大模型生成结构化候选人画像。" />
    <section class="resume-grid">
      <div class="upload-column">
        <div class="content-card upload-card">
          <div class="card-title"><span>01</span><div><h2>上传个人简历</h2><p>支持 PDF、DOCX，文件不超过 10MB</p></div></div>
          <el-upload drag :show-file-list="false" :before-upload="beforeUpload" accept=".pdf,.docx" :disabled="status === 'parsing'">
            <div class="upload-icon">↑</div><div class="upload-text"><b>拖拽简历到此处，或点击上传</b><span>文件仅用于本次岗位胜任力评估</span></div>
          </el-upload>
          <div class="demo-entry"><span>现场演示无需准备文件</span><el-button type="primary" plain @click="loadDemo">一键加载 {{ store.selectedJob }} Demo</el-button></div>
          <div v-if="fileName" class="file-status">
            <div class="file-row"><span class="file-type">{{ fileName.toLowerCase().endsWith('.pdf') ? 'PDF' : 'DOC' }}</span><div><b>{{ fileName }}</b><small>{{ status === 'done' ? '解析完成 · 已生成结构化画像' : steps[Math.max(analysisStep - 1, 0)] + '…' }}</small></div><strong>{{ progress }}%</strong></div>
            <el-progress :percentage="progress" :show-text="false" :status="status === 'done' ? 'success' : ''" />
            <div class="parse-steps"><div v-for="(step,index) in steps" :key="step" :class="{ active: index + 1 === analysisStep, done: index + 1 < analysisStep || status === 'done' }"><i>{{ index + 1 < analysisStep || status === 'done' ? '✓' : index + 1 }}</i><span>{{ step }}</span></div></div>
          </div>
        </div>
        <div class="privacy-note"><span>✓</span><div><b>隐私安全保障</b><p>临时文件在解析完成后立即删除，密钥不会写入代码。</p></div></div>
      </div>

      <transition name="profile">
        <div v-if="status === 'done'" class="content-card profile-card">
          <div class="profile-header"><div class="avatar">{{ avatarText }}</div><div><span>候选人画像</span><h2>{{ store.candidate.name }}</h2><p>{{ store.candidate.education }} · {{ store.candidate.major }}</p></div><span :class="['ready', store.candidate.analysisMode]">{{ store.candidate.analysisMode === 'llm' ? 'AI分析完成' : '本地降级' }}</span></div>
          <el-alert v-if="store.candidate.warning" class="warning" :title="store.candidate.warning" type="warning" :closable="false" show-icon />
          <div class="profile-section"><label>目标方向</label><el-select v-model="store.selectedJob" size="large"><el-option label="Java开发工程师" value="Java开发工程师" /><el-option label="AI算法工程师" value="AI算法工程师" /><el-option label="产品经理" value="产品经理" /></el-select></div>
          <div v-loading="jobLoading" class="job-model"><div class="job-model-head"><div><span>RAG 岗位知识增强</span><b>{{ store.selectedJob }}</b></div><em v-if="store.jobKnowledgeReady">✓ 岗位匹配准备完成</em></div><div class="competency-tags"><span v-for="item in store.jobCompetencies" :key="item.name">{{ item.name }}</span></div></div>
          <div v-loading="jobLoading" class="competency-model-card"><div class="model-title"><div><span>SELF-BUILT MODEL</span><h3>岗位胜任力模型</h3><p>由本项目自主定义，并实际驱动Agent规划、追问与评分</p></div><b>{{ store.competencyModel.length }}维</b></div><div class="model-visual"><div class="model-core">{{ store.selectedJob }}<small>胜任力模型</small></div><span v-for="(item,index) in store.competencyModel.slice(0,5)" :key="item.name" :class="`node node-${index}`">{{ item.name }}</span></div><el-collapse class="model-details"><el-collapse-item v-for="item in store.competencyModel" :key="item.name" :title="item.name" :name="item.name"><p>{{ item.description }}</p><b>评价指标</b><div class="indicator-list"><span v-for="indicator in item.indicators" :key="indicator">✓ {{ indicator }}</span></div><b>评分标准</b><small>{{ item.score_rule }}</small></el-collapse-item></el-collapse></div>
          <div class="profile-section"><label>核心技能</label><div class="tags"><span v-for="skill in store.candidate.skills" :key="skill" class="soft-tag">{{ skill }}</span><span v-if="!store.candidate.skills.length" class="empty-text">未提取到明确技能</span></div></div>
          <div class="profile-section"><label>项目经历</label><div v-if="store.candidate.projects.length" class="projects"><div v-for="project in store.candidate.projects" :key="project.name" class="project-box"><b>{{ project.name }}</b><dl><dt>技术栈</dt><dd>{{ project.technology }}</dd><dt>个人职责</dt><dd>{{ project.responsibility }}</dd><dt>项目结果</dt><dd>{{ project.result }}</dd></dl></div></div><p v-else class="empty-text">简历中未识别到明确项目经历</p></div>
          <div class="insight-grid"><div class="insight good"><span>优势能力</span><p>{{ store.candidate.strength }}</p></div><div class="insight warn"><span>待提升</span><p>{{ store.candidate.weakness }}</p></div></div>
          <div v-if="store.candidate.potentialQuestions.length" class="verify-box"><b>面试待验证</b><span v-for="question in store.candidate.potentialQuestions" :key="question">· {{ question }}</span></div>
          <el-button class="start-button" type="primary" size="large" @click="startInterview">开始 AI 面试 →</el-button>
        </div>
        <div v-else class="content-card empty-profile"><div class="scan-graphic"><i></i><i></i><i></i></div><h3>候选人画像将在这里生成</h3><p>上传简历后，系统将提取文本并调用大模型分析教育、技能和项目经历。</p></div>
      </transition>
    </section>
  </main>
</template>

<style scoped>
.competency-model-card{margin-top:14px;padding:18px;border:1px solid #dce5ff;border-radius:16px;background:linear-gradient(145deg,#f8faff,#fff)}.model-title{display:flex;justify-content:space-between;gap:12px}.model-title span{color:var(--primary);font-size:9px;font-weight:900;letter-spacing:.1em}.model-title h3{margin:4px 0;font-size:16px}.model-title p{margin:0;color:var(--muted);font-size:10px}.model-title>b{align-self:flex-start;padding:6px 9px;border-radius:8px;color:#fff;background:var(--gradient);font-size:10px}.model-visual{position:relative;height:225px;margin:18px 0;border-radius:16px;background:radial-gradient(circle,#e5ebff 0 2px,transparent 3px),linear-gradient(135deg,#f0f4ff,#faf8ff);background-size:25px 25px,auto}.model-core{position:absolute;left:50%;top:50%;width:106px;height:106px;display:grid;place-content:center;transform:translate(-50%,-50%);border:8px solid rgba(255,255,255,.8);border-radius:50%;color:#fff;background:var(--gradient);box-shadow:0 12px 30px rgba(49,95,246,.25);text-align:center;font-size:11px;font-weight:800}.model-core small{display:block;margin-top:4px;font-size:8px;opacity:.75}.model-visual .node{position:absolute;max-width:118px;padding:7px 9px;border:1px solid #dce4fa;border-radius:9px;background:#fff;box-shadow:0 5px 15px rgba(42,62,110,.08);font-size:9px;font-weight:700;text-align:center}.node-0{left:50%;top:10px;transform:translateX(-50%)}.node-1{right:9px;top:58px}.node-2{right:28px;bottom:17px}.node-3{left:28px;bottom:17px}.node-4{left:9px;top:58px}.model-details{border-top:0}.model-details p{margin:0 0 10px;color:#596579;font-size:11px;line-height:1.6}.model-details b,.model-details small{display:block;font-size:10px}.model-details small{margin-top:5px;color:var(--muted);line-height:1.5}.indicator-list{display:flex;gap:5px;flex-wrap:wrap;margin:7px 0 10px}.indicator-list span{padding:5px 7px;border-radius:7px;color:#287459;background:#edf9f4;font-size:9px}
.resume-page{background:radial-gradient(circle at 100% 0,#e4ebff,transparent 26%),#f5f7fb}.resume-grid{display:grid;grid-template-columns:.8fr 1.2fr;gap:24px;align-items:start}.upload-card,.profile-card,.empty-profile{padding:28px}.card-title{display:flex;gap:15px;align-items:flex-start;margin-bottom:24px}.card-title>span{display:grid;place-items:center;width:34px;height:34px;border-radius:10px;color:var(--primary);background:#eef2ff;font-size:12px;font-weight:800}.card-title h2{margin:0;font-size:19px}.card-title p{margin:6px 0 0;color:var(--muted);font-size:13px}.upload-icon{width:58px;height:58px;margin:5px auto 16px;display:grid;place-items:center;border-radius:17px;color:#fff;background:var(--gradient);font-size:27px}.upload-text b,.upload-text span{display:block}.upload-text span{margin-top:8px;color:var(--muted);font-size:12px}.file-status{margin-top:20px;padding:16px;border-radius:14px;background:#f7f9fd}.file-row{display:grid;grid-template-columns:auto 1fr auto;gap:12px;align-items:center;margin-bottom:12px}.file-type{padding:8px;border-radius:8px;color:#fff;background:#e75555;font-size:10px;font-weight:800}.file-row b,.file-row small{display:block}.file-row b{font-size:13px}.file-row small{margin-top:4px;color:var(--muted);font-size:11px}.file-row strong{color:var(--primary);font-size:13px}.parse-steps{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin-top:17px}.parse-steps div{display:flex;align-items:center;gap:5px;color:#a0a8b7;font-size:9px}.parse-steps i{width:18px;height:18px;display:grid;place-items:center;border-radius:50%;background:#e7eaf0;font-style:normal}.parse-steps .active{color:var(--primary);font-weight:700}.parse-steps .active i{color:#fff;background:var(--primary)}.parse-steps .done{color:var(--success)}.parse-steps .done i{color:#fff;background:var(--success)}.privacy-note{display:flex;gap:13px;margin-top:18px;padding:18px;color:#466058;border-radius:15px;background:#eaf8f3}.privacy-note p{margin:5px 0 0;font-size:12px}.profile-header{display:flex;align-items:center;gap:14px;padding-bottom:22px;border-bottom:1px solid var(--line)}.avatar{width:56px;height:56px;display:grid;place-items:center;border-radius:16px;color:#fff;background:var(--gradient);font-size:22px;font-weight:800}.profile-header div:nth-child(2){flex:1}.profile-header span{color:var(--primary);font-size:11px;font-weight:700}.profile-header h2{margin:4px 0;font-size:22px}.profile-header p{margin:0;color:var(--muted);font-size:12px}.profile-header .ready{padding:7px 10px;border-radius:9px;color:var(--success);background:#eaf8f3}.profile-header .ready.fallback{color:#a06b28;background:#fff3df}.warning{margin-top:16px}.profile-section{margin-top:20px}.profile-section>label{display:block;margin-bottom:10px;color:#465065;font-size:12px;font-weight:700}.profile-section .el-select{width:100%}.tags{display:flex;gap:8px;flex-wrap:wrap}.projects{display:grid;gap:11px}.project-box{padding:15px;border-left:3px solid var(--primary);border-radius:0 12px 12px 0;background:#f7f9fd}.project-box>b{font-size:14px}.project-box dl{display:grid;grid-template-columns:58px 1fr;gap:5px 10px;margin:10px 0 0;font-size:12px;line-height:1.55}.project-box dt{color:#8992a4}.project-box dd{margin:0;color:#596579}.insight-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:20px}.insight{padding:15px;border-radius:13px}.insight span{font-size:12px;font-weight:800}.insight p{margin:7px 0 0;font-size:12px;line-height:1.6}.good{color:#287459;background:#edf9f4}.warn{color:#8b612a;background:#fff6e8}.verify-box{display:grid;gap:5px;margin-top:14px;padding:14px;border-radius:12px;background:#f3f5fa;color:#687287;font-size:11px}.verify-box b{color:#3e485b}.start-button{width:100%;margin-top:24px}.empty-text{color:var(--muted);font-size:12px}.empty-profile{min-height:560px;display:grid;place-content:center;text-align:center;color:var(--muted)}.empty-profile h3{color:#4f596c}.empty-profile p{max-width:350px;line-height:1.7}.scan-graphic{width:100px;height:100px;margin:0 auto 18px;padding:25px 20px;border:1px solid #d8e0f4;border-radius:24px;background:#f6f8ff}.scan-graphic i{display:block;height:5px;margin:7px 0;border-radius:5px;background:#cbd6f5}.profile-enter-active{transition:.4s}.profile-enter-from{opacity:0;transform:translateY(15px)}@media(max-width:900px){.resume-grid{grid-template-columns:1fr}}@media(max-width:520px){.insight-grid{grid-template-columns:1fr}.parse-steps{grid-template-columns:1fr 1fr}}
.job-model{min-height:100px;margin-top:14px;padding:15px;border:1px solid #dce5ff;border-radius:14px;background:linear-gradient(135deg,#f5f8ff,#fbfaff)}.job-model-head{display:flex;align-items:center;justify-content:space-between;gap:10px}.job-model-head span,.job-model-head b{display:block}.job-model-head span{color:var(--primary);font-size:10px;font-weight:800}.job-model-head b{margin-top:4px;font-size:14px}.job-model-head em{padding:6px 9px;border-radius:8px;color:var(--success);background:#e8f8f1;font-size:10px;font-style:normal;font-weight:700}.competency-tags{display:flex;gap:7px;flex-wrap:wrap;margin-top:13px}.competency-tags span{padding:6px 9px;border-radius:8px;color:#53617a;background:#fff;border:1px solid #e1e6f1;font-size:10px;font-weight:600}
.demo-entry{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:14px;padding:11px 13px;border-radius:11px;background:#edf2ff;color:#596987;font-size:10px}
</style>
