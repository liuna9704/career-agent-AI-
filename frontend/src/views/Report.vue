<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import PageHeading from '../components/PageHeading.vue'
import { getAssessmentReport } from '../api/report'
import { useAppStore } from '../stores/app'

const router = useRouter()
const store = useAppStore()
const chartRef = ref(null)
const loading = ref(false)
const error = ref('')
const report = ref(null)
let chart

const resize = () => chart?.resize()
const renderChart = async () => {
  await nextTick()
  if (!chartRef.value || !report.value) return
  chart?.dispose()
  chart = echarts.init(chartRef.value)
  const radar = report.value.radar
  chart.setOption({
    tooltip: {},
    radar: {
      indicator: radar.map(item => ({ name: item.name, max: 100 })),
      radius: '66%', splitNumber: 4,
      axisName: { color: '#596579', fontSize: 12 },
      splitArea: { areaStyle: { color: ['#fbfcff', '#f5f7ff'] } },
      splitLine: { lineStyle: { color: '#dce3f2' } },
      axisLine: { lineStyle: { color: '#dce3f2' } },
    },
    series: [{ type: 'radar', data: [{ value: radar.map(item => item.score), name: '能力得分', symbolSize: 7, lineStyle: { width: 3, color: '#315ff6' }, itemStyle: { color: '#315ff6' }, areaStyle: { color: 'rgba(49,95,246,.22)' } }] }],
  })
}

const loadReport = async () => {
  if (!store.interview.sessionId) {
    error.value = '尚未找到有效的面试会话，请先完成AI面试。'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const response = await getAssessmentReport(store.interview.sessionId)
    report.value = response.data
    await renderChart()
    ElMessage.success(response.message)
  } catch (requestError) {
    error.value = requestError.message
  } finally {
    loading.value = false
  }
}

onMounted(() => { window.addEventListener('resize', resize); loadReport() })
onBeforeUnmount(() => { window.removeEventListener('resize', resize); chart?.dispose() })
</script>

<template>
  <main v-loading="loading" class="page report-page" element-loading-text="正在生成评估报告…">
    <el-result v-if="error" icon="warning" title="暂时无法生成报告" :sub-title="error">
      <template #extra><el-button type="primary" @click="router.push('/interview')">开始AI面试</el-button></template>
    </el-result>

    <template v-else-if="report">
      <div class="report-head">
        <PageHeading eyebrow="Assessment Report" title="岗位胜任力评估报告" :description="`${report.candidate.name} · ${report.candidate.job} · 基于本次多轮面试记录生成`" />
        <div class="report-actions"><el-button>导出报告</el-button><router-link to="/resume"><el-button type="primary">重新测评</el-button></router-link></div>
      </div>

      <section class="summary-grid">
        <article class="content-card main-score"><div class="score-ring"><strong>{{ report.summary.score }}</strong><span>综合评分</span></div><div><span class="recommend">{{ report.summary.level }}</span><h2>专业基础扎实，具备良好的工程实践能力</h2><p>候选人与 {{ report.candidate.job }} 岗位整体匹配度较高，建议进入下一轮专业面试。</p></div></article>
        <article class="content-card metric"><span>岗位匹配度</span><strong>{{ report.summary.match_rate }}<small>%</small></strong><el-progress :percentage="report.summary.match_rate" :show-text="false" /><p>岗位核心能力整体匹配</p></article>
        <article class="content-card metric"><span>评估置信度</span><strong>{{ report.summary.confidence }}</strong><div class="confidence"><i></i><i></i><i></i><i></i><i></i></div><p>覆盖 {{ report.radar.length }} 个核心能力维度</p></article>
      </section>

      <section class="analysis-grid">
        <article class="content-card radar-card"><div class="section-head"><div><span>能力画像</span><h2>核心能力雷达图</h2></div><b>岗位均值 75</b></div><div ref="chartRef" class="radar-chart"></div></article>
        <article class="content-card evidence-card"><div class="section-head"><div><span>自建胜任力模型 · 可解释评估</span><h2>能力评分与评价依据</h2></div><b>{{ report.abilities.length }} 项</b></div><div class="score-list"><div v-for="item in report.abilities" :key="item.name" class="score-row"><div class="score-title"><b>{{ item.name }}</b><strong>{{ item.score }}</strong></div><el-progress :percentage="item.score" :show-text="false" :stroke-width="7" /><p>能力证据：{{ item.evidence }}</p><div class="basis-list"><span v-for="basis in item.evaluation_basis" :key="basis">{{ basis }}</span></div><p class="problem">待提升：{{ item.problem }}</p></div></div></article>
      </section>

      <section class="insight-grid">
        <article class="content-card insight strength"><div class="insight-icon">↑</div><div><span>优势分析</span><h3>已验证的核心优势</h3><ul><li v-for="item in report.advantages" :key="item">{{ item }}</li></ul></div></article>
        <article class="content-card insight weakness"><div class="insight-icon">!</div><div><span>主要不足</span><h3>当前岗位能力差距</h3><ul><li v-for="item in report.weaknesses" :key="item">{{ item }}</li></ul></div></article>
        <article class="content-card insight suggestion"><div class="insight-icon">✓</div><div><span>提升建议</span><h3>建议优先执行</h3><ul><li v-for="item in report.suggestions" :key="item">{{ item }}</li></ul></div></article>
      </section>
      <section class="explain-grid">
        <article class="content-card timeline-card"><div class="section-head"><div><span>证据链</span><h2>能力证据时间线</h2></div><b>{{ report.evidence_timeline.length }} 条</b></div><div class="timeline"><div v-for="(item,index) in report.evidence_timeline" :key="index"><i>{{ index + 1 }}</i><div><span>{{ item.ability }}<template v-if="item.project"> · {{ item.project }}</template></span><b>问题：{{ item.question }}</b><p>回答：{{ item.answer }}</p><em>AI判断：{{ item.judgment }}</em></div></div></div></article>
        <article class="content-card verify-card"><div class="section-head"><div><span>真实性验证</span><h2>简历声明 vs 面试验证</h2></div></div><div class="verification"><div v-for="item in report.verifications" :key="item.claim"><b>{{ item.claim }}</b><p>{{ item.verified }}</p><span>可信度 · {{ item.confidence }}</span></div></div></article>
      </section>
      <section class="content-card career-card"><div class="career-title"><span>职业发展建议</span><h2>未来 90 天能力提升路线</h2><p>{{ report.career_advice.recommended_project }}</p></div><div class="career-content"><div><b>推荐学习方向</b><span v-for="item in report.career_advice.learning_directions" :key="item">{{ item }}</span></div><div class="roadmap"><b>成长路线</b><p v-for="(item,index) in report.career_advice.roadmap" :key="item"><i>{{ index + 1 }}</i>{{ item }}</p></div></div></section>
      <footer class="report-footer"><div><b>CareerLens Agent</b><span>AI生成内容仅作为辅助评估依据</span></div><span>会话编号：{{ store.interview.sessionId }}</span></footer>
    </template>
  </main>
</template>

<style scoped>
.basis-list{display:flex;gap:5px;flex-wrap:wrap;margin-top:7px}.basis-list span{padding:5px 7px;border-radius:7px;color:#287459;background:#edf9f4;font-size:9px}
.report-page{min-height:calc(100vh - 72px);background:radial-gradient(circle at 95% 5%,#e3eaff,transparent 24%),#f5f7fb}.report-head{display:flex;justify-content:space-between;align-items:flex-start}.report-actions{display:flex;gap:10px}.summary-grid{display:grid;grid-template-columns:2fr 1fr 1fr;gap:18px}.summary-grid>article{padding:24px}.main-score{display:flex;align-items:center;gap:23px;color:#fff;border:0;background:var(--gradient)}.score-ring{flex:none;width:118px;height:118px;display:grid;place-content:center;text-align:center;border:8px solid rgba(255,255,255,.25);border-radius:50%;background:rgba(255,255,255,.08)}.score-ring strong{font-size:43px;line-height:1}.score-ring span{margin-top:5px;font-size:10px;opacity:.8}.recommend{display:inline-block;padding:6px 10px;border-radius:8px;color:#2651d8;background:#fff;font-size:11px;font-weight:800}.main-score h2{margin:12px 0 7px;font-size:20px}.main-score p{margin:0;opacity:.75;font-size:12px;line-height:1.65}.metric>span{color:var(--muted);font-size:12px}.metric>strong{display:block;margin:15px 0 12px;font-size:37px}.metric>strong small{font-size:17px}.metric p{color:var(--muted);font-size:10px}.confidence{display:flex;gap:5px}.confidence i{width:25px;height:7px;border-radius:8px;background:var(--primary)}.confidence i:last-child{background:#dce2ef}.analysis-grid{display:grid;grid-template-columns:.88fr 1.12fr;gap:18px;margin-top:18px}.radar-card,.evidence-card{padding:24px}.section-head{display:flex;justify-content:space-between}.section-head span{color:var(--primary);font-size:10px;font-weight:800}.section-head h2{margin:5px 0 0;font-size:18px}.section-head>b{height:max-content;padding:6px 9px;border-radius:8px;color:var(--muted);background:#f2f4f8;font-size:10px}.radar-chart{height:410px}.score-list{margin-top:20px}.score-row{margin-bottom:15px}.score-title{display:flex;justify-content:space-between;margin-bottom:6px;font-size:12px}.score-title strong{color:var(--primary)}.score-row p{margin:6px 0 0;color:var(--muted);font-size:10px}.score-row .problem{color:#a06b28}.insight-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:18px}.insight{display:flex;gap:14px;padding:22px}.insight-icon{flex:none;width:35px;height:35px;display:grid;place-items:center;border-radius:11px;font-weight:900}.insight span{font-size:10px;font-weight:800}.insight h3{margin:6px 0 10px;font-size:15px}.insight ul{margin:0;padding-left:17px;color:#657087;font-size:11px;line-height:1.9}.strength .insight-icon{color:#23845f;background:#e6f7f0}.strength span{color:#23845f}.weakness .insight-icon{color:#b36d1d;background:#fff0da}.weakness span{color:#b36d1d}.suggestion .insight-icon{color:#315ff6;background:#eaf0ff}.suggestion span{color:#315ff6}.report-footer{display:flex;justify-content:space-between;margin-top:25px;padding-top:20px;border-top:1px solid #dfe4ed;color:var(--muted);font-size:10px}.report-footer b{margin-right:12px;color:var(--text)}@media(max-width:1000px){.summary-grid{grid-template-columns:1fr 1fr}.main-score{grid-column:1/-1}.analysis-grid{grid-template-columns:1fr}.insight-grid{grid-template-columns:1fr}}@media(max-width:600px){.report-head{display:block}.report-actions{margin-bottom:22px}.summary-grid{grid-template-columns:1fr}.main-score{display:block}.score-ring{margin-bottom:18px}.report-footer{display:block}.report-footer>span{display:block;margin-top:8px}}
.explain-grid{display:grid;grid-template-columns:1.15fr .85fr;gap:18px;margin-top:18px}.timeline-card,.verify-card{padding:24px}.timeline{margin-top:20px}.timeline>div{position:relative;display:flex;gap:13px;padding-bottom:18px}.timeline>div:not(:last-child)::after{position:absolute;left:14px;top:31px;bottom:2px;width:1px;background:#dfe5f2;content:''}.timeline>div>i{z-index:1;flex:none;width:29px;height:29px;display:grid;place-items:center;border-radius:9px;color:#fff;background:var(--gradient);font-size:10px;font-style:normal}.timeline div div{min-width:0}.timeline span{color:var(--primary);font-size:9px;font-weight:800}.timeline b{display:block;margin:4px 0;font-size:11px}.timeline p{margin:0;color:var(--muted);font-size:10px;line-height:1.55}.timeline em{display:inline-block;margin-top:6px;padding:5px 7px;border-radius:6px;color:#267158;background:#e8f8f1;font-size:9px;font-style:normal}.verification{display:grid;gap:11px;margin-top:20px}.verification>div{padding:14px;border:1px solid #e5e9f2;border-radius:12px;background:#fafbfe}.verification b{font-size:11px}.verification p{margin:6px 0;color:#536078;font-size:10px}.verification span{color:var(--success);font-size:9px;font-weight:700}.career-card{display:grid;grid-template-columns:.8fr 1.2fr;gap:30px;margin-top:18px;padding:26px;color:#fff;border:0;background:linear-gradient(135deg,#243d96,#6250c8)}.career-title>span{font-size:10px;font-weight:800;opacity:.7}.career-title h2{margin:8px 0;font-size:21px}.career-title p{margin:0;opacity:.75;font-size:11px;line-height:1.7}.career-content{display:grid;grid-template-columns:1fr 1fr;gap:20px}.career-content b{display:block;margin-bottom:10px;font-size:11px}.career-content>div:first-child span{display:block;margin:7px 0;padding:7px 9px;border-radius:8px;background:rgba(255,255,255,.12);font-size:9px}.roadmap p{display:flex;gap:7px;align-items:center;margin:7px 0;font-size:9px}.roadmap i{width:20px;height:20px;display:grid;place-items:center;border-radius:50%;background:#fff;color:#4252ad;font-style:normal;font-weight:800}@media(max-width:900px){.explain-grid,.career-card{grid-template-columns:1fr}.career-content{grid-template-columns:1fr}}
</style>
