import logging
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from app.agents.interview_agent import interview_agent
from app.agents.state import InterviewState
from app.schemas.interview import AgentTraceItem, InterviewAnalysis, InterviewChatData, InterviewStartData
from app.services.resume_service import resume_service

logger = logging.getLogger("career_agent.interview_service")


@dataclass
class InterviewSession:
    session_id: str
    job: str
    stage: str
    progress: int
    total: int
    ability: str
    current_question: str
    history_questions: list[str] = field(default_factory=list)
    user_answers: list[str] = field(default_factory=list)
    ability_coverage: dict[str, str] = field(default_factory=dict)
    agent_state: dict[str, Any] = field(default_factory=dict)


class InterviewService:
    def __init__(self) -> None:
        self.sessions: dict[str, InterviewSession] = {}

    async def start(self, job: str) -> InterviewStartData:
        session_id = f"session_{uuid4().hex[:12]}"
        candidate = resume_service.latest_profile.model_dump() if resume_service.latest_profile else {
            "name": "候选人", "skills": [], "projects": [], "potential_questions": []
        }
        initial_state: InterviewState = {
            "mode": "start", "session_id": session_id, "candidate_profile": candidate, "job": job,
            "job_context": [], "competency_model": [], "interview_plan": [], "messages": [], "current_stage": "基础能力",
            "current_ability": "岗位基础", "covered_abilities": [], "pending_abilities": [],
            "answer_analysis": {}, "evidences": [], "ability_question_counts": {},
            "current_project_context": {}, "project_question_count": 0,
            "question_count": 0, "total_questions": 10, "next_action": "initial",
            "should_finish": False, "report_data": {}, "agent_mode": "fallback",
        }
        try:
            state = await interview_agent.start(initial_state)
        except Exception as exc:
            logger.exception("[%s] LangGraph start failed, using legacy fallback", session_id)
            state = self._fallback_start(initial_state, exc)
        coverage = self._coverage(state)
        session = InterviewSession(
            session_id=session_id, job=job, stage=state["current_stage"], progress=state["question_count"],
            total=state["total_questions"], ability=state["current_ability"], current_question=state["current_question"],
            history_questions=[state["current_question"]], ability_coverage=coverage, agent_state=dict(state),
        )
        self.sessions[session_id] = session
        logger.info("[%s] session created agent_mode=%s", session_id, state.get("agent_mode"))
        return InterviewStartData(session_id=session_id, job=job, stage=session.stage, progress=session.progress, total=session.total, ability=session.ability, question=session.current_question, ability_coverage=coverage, agent_trace=self._trace(state, initial=True), evidences=[], rag_enhanced=bool(state.get("job_context")), agent_mode=state.get("agent_mode", "fallback"), current_project_context=state.get("current_project_context", {}), technical_points=[])

    async def chat(self, session_id: str, answer: str) -> InterviewChatData | None:
        session = self.sessions.get(session_id)
        if session is None:
            return None
        if session.agent_state.get("should_finish"):
            raw_analysis = session.agent_state.get("answer_analysis", {})
            quality = raw_analysis.get("quality", "normal")
            if quality not in {"good", "normal", "needs_clarification"}:
                quality = "normal"
            return InterviewChatData(
                stage=session.stage, progress=session.progress, total=session.total, ability=session.ability,
                analysis=self._analysis_model(raw_analysis),
                question=session.agent_state.get("report_data", {}).get("summary", "本次面试已完成。"),
                ability_coverage=session.ability_coverage.copy(), completed=True, agent_trace=self._trace(session.agent_state), evidences=self._evidence_labels(session.agent_state), rag_enhanced=bool(session.agent_state.get("job_context")), agent_mode=session.agent_state.get("agent_mode", "fallback"), current_project_context=session.agent_state.get("current_project_context", {}), technical_points=raw_analysis.get("technical_points", []),
            )
        session.user_answers.append(answer)
        try:
            state = await interview_agent.chat(session.agent_state, answer)
        except Exception as exc:
            logger.exception("[%s] LangGraph turn failed, using legacy fallback", session_id)
            state = self._fallback_chat(session.agent_state, answer, exc)
        session.agent_state = dict(state)
        session.stage = state["current_stage"]
        session.progress = min(state.get("question_count", session.progress + 1), session.total)
        session.ability = state["current_ability"]
        completed = bool(state.get("should_finish"))
        question = state.get("current_question", "")
        if completed:
            question = state.get("report_data", {}).get("summary", "本次面试已完成，评估报告正在生成。")
        else:
            session.current_question = question
            session.history_questions.append(question)
        session.ability_coverage = self._coverage(state)
        raw_analysis = state.get("answer_analysis", {})
        quality = raw_analysis.get("quality", "normal")
        if quality not in {"good", "normal", "needs_clarification"}:
            quality = "normal"
        logger.info("[%s] turn complete action=%s stage=%s ability=%s progress=%s", session_id, state.get("next_action"), session.stage, session.ability, session.progress)
        return InterviewChatData(
            stage=session.stage, progress=session.progress, total=session.total, ability=session.ability,
            analysis=self._analysis_model(raw_analysis),
            question=question, ability_coverage=session.ability_coverage.copy(), completed=completed, agent_trace=self._trace(state), evidences=self._evidence_labels(state), rag_enhanced=bool(state.get("job_context")), agent_mode=state.get("agent_mode", "fallback"), current_project_context=state.get("current_project_context", {}), technical_points=raw_analysis.get("technical_points", []),
        )

    @staticmethod
    def _analysis_model(raw: dict[str, Any]) -> InterviewAnalysis:
        quality = raw.get("quality", "normal")
        if quality not in {"good", "normal", "needs_clarification"}:
            quality = "normal"
        evidence = raw.get("evidence", "")
        if isinstance(evidence, list):
            evidence = evidence[0] if evidence else ""
        return InterviewAnalysis(quality=quality, keywords=[str(x) for x in raw.get("keywords", [])], project_detected=str(raw.get("project_detected", "")), ability_detected=str(raw.get("ability_detected", raw.get("ability", ""))), technical_points=[str(x) for x in raw.get("technical_points", [])], evidence=str(evidence), confidence=int(raw.get("confidence", 0) or 0))

    @staticmethod
    def _evidence_labels(state: InterviewState) -> list[str]:
        labels = []
        for item in state.get("evidences", []):
            label = item.get("ability") or item.get("content", "")[:18]
            if label and label not in labels:
                labels.append(label)
        return labels[-6:]

    @staticmethod
    def _trace(state: InterviewState, initial: bool = False) -> list[AgentTraceItem]:
        analysis = state.get("answer_analysis", {})
        items = [AgentTraceItem(label=f"已检索{state.get('job', '目标岗位')}能力模型")]
        if initial:
            items.append(AgentTraceItem(label=f"已生成{len(state.get('interview_plan', []))}项能力面试计划"))
            items.append(AgentTraceItem(label=f"正在考察{state.get('current_ability', '岗位能力')}", status="active"))
            return items
        project = state.get("current_project_context", {}).get("project_name")
        if project:
            items.append(AgentTraceItem(label=f"已锁定当前项目：{project}"))
        for keyword in analysis.get("technical_points", analysis.get("keywords", []))[:3]:
            items.append(AgentTraceItem(label=f"检测到{keyword}技术点"))
        if analysis.get("evidence"):
            items.append(AgentTraceItem(label=f"已记录{state.get('current_ability')}能力证据"))
        action_labels = {"deep_question": "正在深入追问技术细节", "clarify": "正在澄清回答中的缺失信息", "switch_ability": f"已切换至{state.get('current_ability')}能力", "finish": "能力覆盖完成，正在生成报告"}
        items.append(AgentTraceItem(label=action_labels.get(state.get("next_action"), "正在生成下一问题"), status="active"))
        return items

    async def get_job_context(self, job: str, query: str = "岗位核心能力与面试考察点") -> list[dict]:
        from app.services.rag_service import rag_service
        return await rag_service.search(job, query, top_k=4)

    @staticmethod
    def _coverage(state: InterviewState) -> dict[str, str]:
        plan = [item.get("ability") for item in state.get("interview_plan", []) if item.get("ability")]
        coverage = {ability: "pending" for ability in plan}
        for ability in state.get("covered_abilities", []):
            coverage[ability] = "covered"
        if not state.get("should_finish") and state.get("current_ability"):
            coverage[state["current_ability"]] = "active"
        return coverage

    @staticmethod
    def _fallback_start(state: InterviewState, error: Exception) -> InterviewState:
        question = "请结合简历介绍一个最有代表性的项目，并说明你的个人职责和技术决策。"
        return {**state, "interview_plan": [
            {"stage": "基础能力", "ability": "Java基础", "reason": "岗位基础"},
            {"stage": "项目深入追问", "ability": "Spring Boot", "reason": "项目框架"},
            {"stage": "项目深入追问", "ability": "Redis", "reason": "缓存能力"},
            {"stage": "压力测试", "ability": "分布式系统", "reason": "架构能力"},
        ], "current_stage": "基础能力", "current_ability": "Java基础", "pending_abilities": ["Spring Boot", "Redis", "分布式系统"], "current_question": question, "messages": [{"role": "assistant", "content": question, "ability": "Java基础"}], "question_count": 1, "agent_mode": "fallback", "decision_reason": str(error)}

    @staticmethod
    def _fallback_chat(state: InterviewState, answer: str, error: Exception) -> InterviewState:
        lowered = answer.lower()
        context = dict(state.get("current_project_context", {}))
        project_match = next((str(item.get("name")) for item in state.get("candidate_profile", {}).get("projects", []) if item.get("name") and str(item.get("name")) in answer), "")
        if project_match and not context.get("project_name"):
            context["project_name"] = project_match
        project = context.get("project_name", "当前项目")
        if "大模型" in answer or "llm api" in lowered:
            ability, points = "AI应用开发能力", [x for x in ["FastAPI" if "fastapi" in lowered else "", "LLM API"] if x]
            question = f"在{project}中，FastAPI调用LLM API时如何处理超时、失败重试与结果可信度？"
        elif "vue3" in lowered or "前端" in answer:
            ability, points = "前端工程能力", [x for x in ["Vue3" if "vue3" in lowered else "", "地图展示" if "地图" in answer else "", "机器人状态监控" if "状态监控" in answer else ""] if x]
            question = f"在{project}中，你如何拆分Vue3组件并管理地图、机器人状态和接口调用？"
        elif "fastapi" in lowered:
            ability, points = "后端接口开发能力", ["FastAPI"]
            question = f"在{project}中，FastAPI接口分层、异常处理和数据契约如何设计？"
        elif "redis" in lowered:
            points = ["Redis"]
            ability, question = "Redis", "你提到了Redis缓存，请说明缓存一致性和分布式锁如何设计？"
        elif "spring boot" in lowered:
            points = ["Spring Boot"]
            ability, question = "Spring Boot", "为什么选择Spring Boot？事务边界和异常回滚如何设计？"
        else:
            points = []
            ability, question = state.get("current_ability", "Java基础"), "请补充具体实现细节、个人贡献和量化结果。"
        context["technologies"] = list(dict.fromkeys([*context.get("technologies", []), *points]))
        evidence = {"ability": ability, "content": answer[:220], "question": state.get("current_question", ""), "project": context.get("project_name", ""), "technical_points": points, "confidence": 75, "missing": []}
        analysis = {"quality": "good" if len(answer) > 20 else "needs_clarification", "ability": ability, "ability_detected": ability, "project_detected": context.get("project_name", ""), "technical_points": points, "keywords": points, "evidence": answer[:220], "confidence": 75}
        return {**state, "messages": [*state.get("messages", []), {"role": "user", "content": answer}, {"role": "assistant", "content": question, "ability": ability, "project": context.get("project_name", "")}], "current_ability": ability, "current_project_context": context, "current_question": question, "question_count": min(state.get("question_count", 1) + 1, 10), "answer_analysis": analysis, "evidences": [*state.get("evidences", []), evidence], "agent_mode": "fallback", "decision_reason": str(error)}


interview_service = InterviewService()
