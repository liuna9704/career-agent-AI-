<script setup>
const steps = [
  { number: '01', title: '简历解析', text: '识别技能、项目经历与候选人优势' },
  { number: '02', title: '岗位匹配', text: 'RAG检索岗位标准，定位能力差距' },
  { number: '03', title: 'AI面试', text: '结合实时回答进行动态深入追问' },
  { number: '04', title: '能力评估', text: '基于回答证据生成专业评估报告' },
]
</script>

<template>
  <main class="home-page">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow"><span></span> CAREERLENS AGENT · AI 面试官</p>
        <h1>让每一次面试，<br /><em>看见真实能力</em></h1>
        <p class="subtitle">融合简历解析、岗位知识增强、多轮智能追问与证据链评估，打造真正懂岗位的 AI 胜任力评估智能体。</p>
        <div class="hero-actions">
          <router-link to="/resume"><el-button type="primary" size="large" round>上传简历，开始面试 →</el-button></router-link>
          <span>已支持 3 类核心岗位</span>
        </div>
      </div>
      <div class="agent-visual">
        <div class="orbit orbit-one"></div><div class="orbit orbit-two"></div>
        <div class="agent-core"><span>AI</span><small>面试官在线</small></div>
        <div class="float-card card-a"><b>动态追问</b><small>回答驱动 · 非固定题库</small></div>
        <div class="float-card card-b"><b>82%</b><small>岗位匹配度</small></div>
      </div>
    </section>
    <section class="flow-section">
      <div class="section-title"><span>完整评估闭环</span><h2>从一份简历，到一份可信报告</h2></div>
      <div class="flow-grid">
        <article v-for="step in steps" :key="step.number"><span>{{ step.number }}</span><h3>{{ step.title }}</h3><p>{{ step.text }}</p></article>
      </div>
    </section>
    <section class="tech-section"><div class="section-title"><span>AI NATIVE ARCHITECTURE</span><h2>不只是聊天，而是可解释的面试智能体</h2></div><div class="tech-grid"><article><i>🤖</i><b>LangGraph Agent</b><p>规划、分析、决策与追问节点协同，动态控制多轮面试。</p></article><article><i>📚</i><b>RAG 知识增强</b><p>FAISS检索岗位能力模型、评分标准和专业追问方向。</p></article><article><i>🧠</i><b>LLM 深度理解</b><p>理解简历、识别技术细节，并分析回答深度与可信度。</p></article><article><i>📊</i><b>能力证据评估</b><p>从每轮回答提取证据，形成可追溯、可解释的专业报告。</p></article></div></section>
  </main>
</template>

<style scoped>
.home-page { min-height: calc(100vh - 72px); overflow: hidden; background: radial-gradient(circle at 82% 18%, #dde7ff, transparent 26%), linear-gradient(180deg, #fbfcff, #f3f6fd); }
.hero { min-height: 610px; padding: 70px max(7vw, 24px) 55px; display: grid; grid-template-columns: 1.15fr .85fr; align-items: center; gap: 40px; }
.eyebrow { color: var(--primary); font-size: 12px; font-weight: 800; letter-spacing: .12em; }
.eyebrow span { display: inline-block; width: 7px; height: 7px; margin-right: 8px; border-radius: 50%; background: var(--success); box-shadow: 0 0 0 5px rgba(32,173,118,.12); }
h1 { margin: 23px 0 26px; font-size: clamp(48px, 6vw, 82px); line-height: 1.08; letter-spacing: -.06em; }
h1 em { color: var(--primary); font-style: normal; }
.subtitle { max-width: 700px; color: #667085; font-size: 18px; line-height: 1.9; }
.hero-actions { margin-top: 34px; display: flex; align-items: center; gap: 22px; color: var(--muted); font-size: 13px; }
.agent-visual { position: relative; min-height: 400px; display: grid; place-items: center; }
.agent-core { position: relative; z-index: 2; width: 170px; height: 170px; display: grid; place-content: center; text-align: center; border: 12px solid rgba(255,255,255,.72); border-radius: 50%; color: white; background: var(--gradient); box-shadow: 0 30px 80px rgba(58,80,194,.34); }
.agent-core span { font-size: 48px; font-weight: 900; }.agent-core small { margin-top: 5px; opacity: .8; }
.orbit { position: absolute; border: 1px solid rgba(49,95,246,.18); border-radius: 50%; }.orbit-one { width: 290px; height: 290px; }.orbit-two { width: 390px; height: 390px; }
.float-card { position: absolute; z-index: 3; padding: 17px 20px; border: 1px solid rgba(49,95,246,.12); border-radius: 16px; background: rgba(255,255,255,.92); box-shadow: 0 16px 45px rgba(53,70,130,.15); }.float-card b,.float-card small { display: block; }.float-card small { margin-top: 5px; color: var(--muted); }.card-a { left: 0; top: 62px; }.card-b { right: 3%; bottom: 54px; }.card-b b { color: var(--primary); font-size: 25px; }
.flow-section { padding: 70px max(7vw, 24px) 90px; background: #fff; }.section-title span { color: var(--primary); font-weight: 700; font-size: 12px; }.section-title h2 { margin: 10px 0 30px; font-size: 30px; }
.flow-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 18px; }.flow-grid article { padding: 25px; border: 1px solid var(--line); border-radius: 18px; background: #fbfcff; }.flow-grid article > span { color: var(--primary); font-weight: 800; }.flow-grid h3 { margin: 23px 0 9px; }.flow-grid p { color: var(--muted); line-height: 1.65; font-size: 14px; }
@media(max-width:900px){.hero{grid-template-columns:1fr}.agent-visual{display:none}.flow-grid{grid-template-columns:1fr 1fr}}@media(max-width:520px){.flow-grid{grid-template-columns:1fr}.hero-actions{align-items:flex-start;flex-direction:column}}
.tech-section{padding:75px max(7vw,24px) 95px;background:#17233d;color:#fff}.tech-section .section-title span{color:#8eabff}.tech-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.tech-grid article{padding:25px;border:1px solid rgba(255,255,255,.1);border-radius:18px;background:rgba(255,255,255,.045)}.tech-grid i{display:block;margin-bottom:22px;font-size:28px;font-style:normal}.tech-grid b{font-size:15px}.tech-grid p{margin:10px 0 0;color:#aeb9cf;font-size:12px;line-height:1.75}@media(max-width:800px){.tech-grid{grid-template-columns:1fr 1fr}}@media(max-width:480px){.tech-grid{grid-template-columns:1fr}}
</style>
