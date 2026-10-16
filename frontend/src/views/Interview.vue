<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { startInterview, sendInterviewMessage } from '../api/interview'
import { useAppStore } from '../stores/app'

const router = useRouter(), store = useAppStore()
const input = ref(''), loading = ref(true), sending = ref(false), typingQuestion = ref(false), messageArea = ref(null)
const stages = ['基础能力', '项目深入追问', '业务场景', '压力测试']
const shortStages = ['基础能力', '项目深入', '场景分析', '压力测试']
const interview = computed(() => store.interview)
const stageIndex = computed(() => Math.max(0, stages.indexOf(interview.value.stage)))
const percentage = computed(() => Math.round(interview.value.progress / interview.value.total * 100) || 0)
const abilities = computed(() => Object.entries(interview.value.abilityCoverage).map(([name, state]) => ({ name, state })))
const thinkingLabel = computed(() => sending.value ? '正在分析回答' : typingQuestion.value ? '正在生成问题' : '等待候选人回答')
const scrollBottom = async () => { await nextTick(); if (messageArea.value) messageArea.value.scrollTop = messageArea.value.scrollHeight }

const typeQuestion = async message => {
  const fullText = message.text
  message.text = ''
  typingQuestion.value = true
  for (let i = 0; i < fullText.length; i += 1) {
    message.text += fullText[i]
    if (i % 4 === 0) await new Promise(resolve => window.setTimeout(resolve, 12))
  }
  typingQuestion.value = false
  await scrollBottom()
}

const createSession = async () => {
  loading.value = true; store.resetInterview()
  try {
    const response = await startInterview(store.selectedJob)
    store.initializeInterview(response.data)
    await typeQuestion(interview.value.messages.at(-1))
  } catch (error) { ElMessage.error(error.message) }
  finally { loading.value = false }
}

const send = async () => {
  const answer = input.value.trim()
  if (!answer || sending.value || !interview.value.sessionId) return
  store.addInterviewMessage({ role: 'user', text: answer }); input.value = ''; sending.value = true; await scrollBottom()
  try {
    const response = await sendInterviewMessage({ session_id: interview.value.sessionId, answer })
    store.updateInterview(response.data)
    const message = { role: 'ai', text: response.data.question, tag: response.data.ability }
    store.addInterviewMessage(message); sending.value = false; await typeQuestion(message)
    if (response.data.completed) ElMessage.success('面试完成，能力证据报告已生成')
  } catch (error) { ElMessage.error(error.message); sending.value = false }
}
const finish = () => router.push('/report')
onMounted(createSession)
</script>

<template>
  <main v-loading="loading" class="interview-page" element-loading-text="Agent正在规划面试…">
    <aside class="left-panel">
      <div class="interviewer-card">
        <div class="avatar-wrap"><div class="pulse"></div><div class="ai-avatar">CL</div><span></span></div>
        <h2>CareerLens AI</h2><p>Interviewer · 智能面试官</p>
        <div class="ai-status"><i></i>{{ thinkingLabel }}</div>
      </div>
      <div class="meta-list"><label>目标岗位</label><b>{{ interview.job || store.selectedJob }}</b><label>当前考察</label><span class="ability-chip">{{ interview.ability }}</span><label>当前项目</label><b class="project-name">{{ interview.projectContext?.project_name || '等待回答识别' }}</b><label>已识别技术</label><div class="tech-tags"><span v-for="item in interview.technicalPoints" :key="item">{{ item }}</span><small v-if="!interview.technicalPoints.length">回答后动态提取</small></div><label>面试进度</label><div class="progress-title"><span>{{ interview.progress }}/{{ interview.total }}</span><span>{{ percentage }}%</span></div><el-progress :percentage="percentage" :show-text="false" /><label>Agent模式</label><small class="mode">{{ interview.agentMode === 'llm' ? 'LLM自主推理' : '安全降级模式' }} · RAG {{ interview.ragEnhanced ? '已增强' : '准备中' }}</small></div>
      <el-button plain @click="finish">结束并生成报告</el-button>
    </aside>

    <section class="chat-panel">
      <div class="stage-strip"><div v-for="(stage,index) in shortStages" :key="stage" :class="{ active:index===stageIndex, done:index<stageIndex }"><i>{{ index < stageIndex ? '✓' : index + 1 }}</i><span>阶段{{ index + 1 }}<b>{{ stage }}</b></span></div></div>
      <div ref="messageArea" class="messages">
        <div v-for="(message,index) in interview.messages" :key="index" :class="['message',message.role]"><div class="message-avatar">{{ message.role === 'ai' ? 'AI' : '我' }}</div><div><span class="speaker">{{ message.role === 'ai' ? 'CareerLens AI Interviewer' : store.candidate.name }}</span><div class="bubble">{{ message.text }}<i v-if="message.role==='ai' && typingQuestion && index===interview.messages.length-1" class="cursor"></i></div><small v-if="message.tag">考察维度 · {{ message.tag }}</small></div></div>
        <div v-if="sending" class="message ai"><div class="message-avatar thinking">AI</div><div><span class="speaker">Agent正在分析回答</span><div class="bubble dots"><i></i><i></i><i></i><span>分析技术点 · 匹配岗位标准 · 决策下一动作</span></div></div></div>
      </div>
      <div class="composer"><textarea v-model="input" rows="3" :disabled="sending || typingQuestion || interview.completed" :placeholder="interview.completed ? '面试已完成，请查看评估报告' : '结合具体项目、技术决策和量化结果回答…'" @keydown.enter.exact.prevent="send"></textarea><div><span>Enter 发送 · Shift + Enter 换行</span><el-button v-if="!interview.completed" type="primary" :loading="sending" @click="send">发送回答 ↑</el-button><el-button v-else type="success" @click="finish">查看评估报告</el-button></div></div>
    </section>

    <aside class="right-panel">
      <section class="agent-process"><header><span>AGENT LIVE</span><b>智能决策过程</b></header><div class="brain"><span>🧠</span><div><b>{{ thinkingLabel }}</b><small>不展示内部Prompt，仅呈现可解释动作</small></div></div><div class="trace"><div v-for="item in interview.agentTrace" :key="item.label" :class="item.status"><i>{{ item.status === 'active' ? '↻' : '✓' }}</i><span>{{ item.label }}</span></div></div></section>
      <section class="evidence-panel"><header><span>能力证据</span><b>{{ interview.evidences.length }} 项</b></header><div class="evidence-tags"><span v-for="item in interview.evidences" :key="item">{{ item }}</span><small v-if="!interview.evidences.length">回答后将自动提取证据</small></div></section>
      <section class="ability-panel"><header><span>能力覆盖</span><b>{{ abilities.filter(x=>x.state==='covered').length }}/{{ abilities.length }}</b></header><div v-for="ability in abilities" :key="ability.name" class="ability-row"><i :class="ability.state">{{ ability.state==='covered'?'✓':ability.state==='active'?'↻':'·' }}</i><span>{{ ability.name }}</span></div></section>
    </aside>
  </main>
</template>

<style scoped>
.project-name{color:#34405a;line-height:1.5}.tech-tags{display:flex;gap:5px;flex-wrap:wrap}.tech-tags span{padding:5px 7px;border-radius:7px;color:#315ff6;background:#edf2ff;font-size:9px}.tech-tags small{color:var(--muted);font-size:9px}
.interview-page{height:calc(100vh - 72px);min-height:680px;display:grid;grid-template-columns:245px 1fr 310px;background:#f5f7fb}.left-panel,.right-panel{padding:22px;border-right:1px solid var(--line);background:#fff;overflow:auto}.right-panel{border:0;border-left:1px solid var(--line)}.interviewer-card{text-align:center;padding:12px 0 22px;border-bottom:1px solid var(--line)}.avatar-wrap{position:relative;width:94px;height:94px;margin:auto}.ai-avatar{position:relative;z-index:2;width:94px;height:94px;display:grid;place-items:center;border:8px solid #edf1ff;border-radius:30px;color:#fff;background:var(--gradient);box-shadow:0 15px 35px rgba(49,95,246,.25);font-size:26px;font-weight:900}.pulse{position:absolute;inset:0;border-radius:30px;background:#cfdcff;animation:pulse 2s infinite}@keyframes pulse{50%{transform:scale(1.16);opacity:0}}.avatar-wrap>span{position:absolute;z-index:4;right:0;bottom:5px;width:16px;height:16px;border:3px solid #fff;border-radius:50%;background:#20ad76}.interviewer-card h2{margin:14px 0 3px;font-size:17px}.interviewer-card p{margin:0;color:var(--muted);font-size:10px}.ai-status{display:inline-flex;align-items:center;gap:6px;margin-top:12px;padding:7px 10px;border-radius:9px;color:#315ff6;background:#edf2ff;font-size:10px;font-weight:700}.ai-status i{width:6px;height:6px;border-radius:50%;background:#315ff6;animation:blink 1s infinite}@keyframes blink{50%{opacity:.2}}.meta-list{padding:18px 0}.meta-list label,.meta-list b{display:block}.meta-list label{margin:16px 0 7px;color:var(--muted);font-size:10px}.meta-list label:first-child{margin-top:0}.meta-list b{font-size:12px}.ability-chip{display:inline-flex;padding:7px 9px;border-radius:8px;color:var(--primary);background:#edf2ff;font-size:10px;font-weight:700}.progress-title{display:flex;justify-content:space-between;margin-bottom:6px;font-size:10px}.mode{color:#69758c;font-size:9px}.left-panel>.el-button{width:100%}.chat-panel{display:grid;grid-template-rows:auto 1fr auto;min-width:0}.stage-strip{height:76px;padding:0 26px;display:grid;grid-template-columns:repeat(4,1fr);align-items:center;border-bottom:1px solid var(--line);background:#fff}.stage-strip>div{position:relative;display:flex;align-items:center;gap:8px;color:#a2aaba}.stage-strip>div:not(:last-child)::after{position:absolute;left:36px;right:10px;top:14px;height:1px;background:#e4e8ef;content:''}.stage-strip i{position:relative;z-index:2;width:28px;height:28px;display:grid;place-items:center;border-radius:50%;background:#edf0f4;font-size:10px;font-style:normal}.stage-strip span,.stage-strip b{display:block}.stage-strip span{font-size:8px}.stage-strip b{margin-top:2px;font-size:10px}.stage-strip .active{color:var(--primary)}.stage-strip .active i{color:#fff;background:var(--primary);box-shadow:0 0 0 5px #e9eeff}.stage-strip .done{color:var(--success)}.stage-strip .done i{color:#fff;background:var(--success)}.messages{padding:27px;overflow-y:auto}.message{display:flex;gap:11px;max-width:84%;margin-bottom:24px}.message.user{margin-left:auto;flex-direction:row-reverse}.message-avatar{flex:none;width:35px;height:35px;display:grid;place-items:center;border-radius:11px;color:#fff;background:var(--gradient);font-size:10px;font-weight:800}.user .message-avatar{background:#27344e}.speaker{display:block;margin-bottom:6px;color:var(--muted);font-size:9px}.user .speaker{text-align:right}.bubble{padding:14px 17px;border-radius:4px 16px 16px 16px;background:#fff;box-shadow:0 6px 22px rgba(46,60,100,.08);font-size:13px;line-height:1.75}.user .bubble{color:#fff;border-radius:16px 4px 16px 16px;background:#315ff6}.message small{display:block;margin-top:6px;color:#9199a9;font-size:9px}.cursor{display:inline-block;width:2px;height:14px;margin-left:2px;vertical-align:middle;background:#315ff6;animation:blink .7s infinite}.dots i{display:inline-block;width:6px;height:6px;margin-right:5px;border-radius:50%;background:#7183ba;animation:dot 1s infinite}.dots i:nth-child(2){animation-delay:.15s}.dots i:nth-child(3){animation-delay:.3s}.dots span{margin-left:5px;color:#8490a8;font-size:9px}@keyframes dot{50%{transform:translateY(-5px)}}.composer{margin:0 24px 20px;padding:12px 14px;border:1px solid #dce2ee;border-radius:16px;background:#fff;box-shadow:0 10px 30px rgba(43,64,116,.08)}.composer textarea{width:100%;border:0;outline:0;resize:none;background:transparent}.composer>div{display:flex;align-items:center;justify-content:space-between}.composer span{color:var(--muted);font-size:9px}.right-panel section{margin-bottom:17px;padding-bottom:17px;border-bottom:1px solid var(--line)}.right-panel header{display:flex;align-items:center;justify-content:space-between}.right-panel header span{color:var(--primary);font-size:9px;font-weight:800;letter-spacing:.08em}.right-panel header b{font-size:12px}.brain{display:flex;gap:10px;align-items:center;margin:13px 0;padding:12px;border-radius:12px;background:linear-gradient(135deg,#edf2ff,#f7f3ff)}.brain>span{font-size:22px}.brain b,.brain small{display:block}.brain b{font-size:11px}.brain small{margin-top:3px;color:var(--muted);font-size:8px}.trace{display:grid;gap:8px}.trace>div{display:flex;gap:8px;align-items:center;color:#596579;font-size:10px}.trace i{width:19px;height:19px;display:grid;place-items:center;border-radius:6px;color:#fff;background:var(--success);font-style:normal;font-size:9px}.trace .active i{background:var(--primary);animation:spinColor 1.3s infinite}@keyframes spinColor{50%{box-shadow:0 0 0 4px #e7edff}}.evidence-tags{display:flex;gap:6px;flex-wrap:wrap;margin-top:12px}.evidence-tags span{padding:6px 8px;border-radius:8px;color:#2e7059;background:#eaf8f3;font-size:9px}.evidence-tags small{color:var(--muted);font-size:9px}.ability-panel{border-bottom:0!important}.ability-row{display:flex;gap:9px;align-items:center;padding:8px 0;color:#69758b;font-size:10px}.ability-row i{width:22px;height:22px;display:grid;place-items:center;border-radius:7px;background:#eef1f5;font-style:normal}.ability-row i.covered{color:#fff;background:var(--success)}.ability-row i.active{color:#fff;background:var(--primary)}@media(max-width:1100px){.interview-page{grid-template-columns:220px 1fr}.right-panel{display:none}}@media(max-width:720px){.interview-page{display:block}.left-panel{display:none}.chat-panel{height:calc(100vh - 134px)}.stage-strip{padding:0 12px}.stage-strip span{display:none}.message{max-width:95%}}
</style>
