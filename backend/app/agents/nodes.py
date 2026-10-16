import json
import logging
import re
from typing import Any, Callable

from app.agents.prompts import build_analyze_prompt, build_decision_prompt, build_planner_prompt, build_question_prompt, build_report_prompt
from app.agents.state import InterviewState
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service

logger = logging.getLogger("career_agent.interview_agent")

TECHNOLOGY_ALIASES = {
    "Vue3": ("vue3", "vue 3"), "Vue": ("vue",), "Pinia": ("pinia",),
    "Axios": ("axios",), "FastAPI": ("fastapi",), "Node.js": ("node.js", "nodejs"),
    "LLM API": ("llm api", "大模型", "模型接口"), "Spring Boot": ("spring boot", "springboot"),
    "Redis": ("redis",), "MySQL": ("mysql",), "Docker": ("docker",),
    "地图展示": ("地图展示", "地图渲染"), "机器人状态监控": ("机器人状态监控", "状态监控"),
    "远程控制": ("远程控制",), "分布式锁": ("分布式锁",), "缓存一致性": ("缓存一致性",),
}


def _technical_points(answer: str) -> list[str]:
    lowered = answer.lower()
    return [name for name, aliases in TECHNOLOGY_ALIASES.items() if any(alias in lowered for alias in aliases)]


def _detect_project(state: InterviewState, answer: str) -> str:
    for project in state.get("candidate_profile", {}).get("projects", []):
        name = str(project.get("name", "")).strip()
        if name and name in answer:
            return name
    match = re.search(r"(?:负责(?:开发|建设|参与)?|在)([\u4e00-\u9fa5A-Za-z0-9·_-]{2,30}?(?:管理平台|平台|系统|项目))", answer)
    return match.group(1) if match else ""


def _detect_ability(answer: str, points: list[str], default: str) -> str:
    lowered = answer.lower()
    if "LLM API" in points or "调用大模型" in answer or "智能分析" in answer:
        return "AI应用开发能力"
    if any(item in points for item in ("Vue3", "Vue", "Pinia", "Axios", "地图展示", "机器人状态监控", "远程控制")) or "前端" in answer or "页面" in answer:
        return "前端工程能力"
    if "FastAPI" in points or "Node.js" in points or "后端" in answer or "接口开发" in answer:
        return "后端接口开发能力"
    if "Redis" in points or "缓存一致性" in points or "分布式锁" in points:
        return "缓存与分布式能力"
    if "Spring Boot" in points or "Java" in lowered:
        return "Java后端工程能力"
    return default


def _merge_project_context(state: InterviewState, answer: str, analysis: dict[str, Any]) -> tuple[dict[str, Any], int]:
    current = dict(state.get("current_project_context", {}))
    detected = str(analysis.get("project_detected", "")).strip()
    current_name = str(current.get("project_name", "")).strip()
    # 当前项目至少连续深入两轮；LLM偶然返回其他简历项目时不允许覆盖。
    if detected and (not current_name or detected == current_name or state.get("project_question_count", 0) >= 2 and state.get("next_action") == "switch_ability"):
        current["project_name"] = detected
    points = list(dict.fromkeys([*current.get("technologies", []), *analysis.get("technical_points", [])]))
    current["technologies"] = points
    ability = analysis.get("ability_detected", "")
    if ability == "前端工程能力":
        current["role"] = "前端开发"
    elif ability == "后端接口开发能力":
        current["role"] = "后端开发"
    elif ability == "AI应用开发能力":
        current["role"] = "AI应用开发"
    count = state.get("project_question_count", 0) + 1 if current.get("project_name") else 0
    return current, count


def _json_object(raw: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("LLM响应中没有JSON对象")
    return json.loads(cleaned[start : end + 1])


async def _structured_call(prompt: str, fallback: Callable[[], dict]) -> tuple[dict, str]:
    try:
        return _json_object(await llm_service.chat(prompt)), "llm"
    except Exception as exc:
        logger.warning("LLM node fallback: %s", exc)
        return fallback(), "fallback"


def _stage_for_ability(state: InterviewState, ability: str) -> str:
    for item in state.get("interview_plan", []):
        if item.get("ability") == ability:
            return item.get("stage", "项目深入追问")
    return "项目深入追问"


async def planner_node(state: InterviewState) -> dict:
    competency_model = rag_service.get_competency_model(state["job"])["competencies"]
    competencies = competency_model or rag_service.get_competencies(state["job"])["competencies"]
    try:
        context = await rag_service.search(state["job"], "岗位核心能力 面试考察点 评分标准", top_k=5)
    except Exception as exc:
        logger.warning("Planner RAG fallback: %s", exc)
        context = []

    def fallback() -> dict:
        names = [item["name"] for item in competencies]
        skills = " ".join(state.get("candidate_profile", {}).get("skills", [])).lower()
        prioritized = [name for name in names if name.lower() in skills]
        prioritized += [name for name in names if name not in prioritized]
        prioritized = prioritized[:6]
        stages = ["基础能力", "项目深入追问", "项目深入追问", "业务场景", "压力测试", "压力测试"]
        return {"plan": [{"stage": stages[index], "ability": ability, "reason": "岗位核心能力与简历技能匹配"} for index, ability in enumerate(prioritized)]}

    payload, mode = await _structured_call(build_planner_prompt(state.get("candidate_profile", {}), state["job"], competencies), fallback)
    plan = [item for item in payload.get("plan", []) if item.get("ability")]
    if not plan:
        plan = fallback()["plan"]
        mode = "fallback"
    current = plan[0]["ability"]
    logger.info("[%s] plan=%s mode=%s", state["session_id"], [item["ability"] for item in plan], mode)
    return {
        "job_context": context,
        "competency_model": competency_model,
        "interview_plan": plan,
        "current_stage": plan[0].get("stage", "基础能力"),
        "current_ability": current,
        "covered_abilities": [],
        "pending_abilities": [item["ability"] for item in plan[1:]],
        "ability_question_counts": {},
        "evidences": [],
        "answer_analysis": {},
        "current_project_context": {},
        "project_question_count": 0,
        "next_action": "initial",
        "should_finish": False,
        "agent_mode": mode,
    }


async def question_node(state: InterviewState) -> dict:
    ability = state["current_ability"]
    try:
        context = await rag_service.search(state["job"], f"{ability} 考察目标 追问方向 优秀回答", top_k=2)
    except Exception as exc:
        logger.warning("Question RAG fallback: %s", exc)
        context = state.get("job_context", [])[:2]
    model_item = next((item for item in state.get("competency_model", []) if item.get("name") == ability), None)
    if model_item:
        context = [{"source": "competency_model", "ability": ability, "content": model_item}, *context]

    def fallback() -> dict:
        answer = next((item.get("content", "") for item in reversed(state.get("messages", [])) if item.get("role") == "user"), "")
        action = state.get("next_action", "initial")
        lowered = answer.lower()
        project_context = state.get("current_project_context", {})
        project = project_context.get("project_name") or (state.get("candidate_profile", {}).get("projects") or [{}])[0].get("name", "简历项目")
        points = state.get("answer_analysis", {}).get("technical_points", [])
        if action == "clarify":
            question = f"你刚才对{ability}的说明还比较概括，请结合具体项目、个人职责和量化结果进一步说明。"
        elif ability == "前端工程能力" and project_context.get("project_name"):
            question = f"在{project}中，你如何拆分Vue3组件，并管理机器人状态、地图渲染与远程控制的状态和接口调用？"
        elif ability == "AI应用开发能力" and project_context.get("project_name"):
            question = f"在{project}中，FastAPI调用LLM API的请求链路如何设计，并如何处理超时、失败重试与结果可信度？"
        elif ability == "后端接口开发能力" and project_context.get("project_name"):
            question = f"在{project}中，FastAPI接口的分层、异常处理和前后端数据契约是如何设计的？"
        elif "redis" in lowered or ability == "Redis":
            question = "你提到了Redis缓存，请结合项目说明缓存与数据库一致性如何保证，分布式锁又如何避免误删和过期问题？"
        elif "spring boot" in lowered or ability == "Spring Boot":
            question = "你为什么选择Spring Boot作为项目框架？请进一步说明事务边界和异常回滚是如何设计的。"
        elif action == "deep_question" and answer:
            keyword = (points or state.get("answer_analysis", {}).get("keywords") or [ability])[0]
            question = f"在{project}中，你提到了{keyword}，请解释技术选型依据、实现细节和最终验证结果。"
        else:
            question = f"结合你的{project}经历，请说明你在{ability}方面做过的具体工作、技术决策和结果。"
        return {"question": question}

    payload, mode = await _structured_call(build_question_prompt(state, context), fallback)
    question = str(payload.get("question", "")).strip() or fallback()["question"]
    locked_project = state.get("current_project_context", {}).get("project_name", "")
    other_projects = [str(item.get("name", "")) for item in state.get("candidate_profile", {}).get("projects", []) if item.get("name") and item.get("name") != locked_project]
    if locked_project and (locked_project not in question or any(name in question for name in other_projects)):
        logger.warning("[%s] rejected cross-project question while locked to %s", state["session_id"], locked_project)
        question, mode = fallback()["question"], "fallback"
    messages = [*state.get("messages", []), {"role": "assistant", "content": question, "ability": ability, "project": state.get("current_project_context", {}).get("project_name", "")}]
    counts = dict(state.get("ability_question_counts", {}))
    counts[ability] = counts.get(ability, 0) + 1
    logger.info("[%s] question #%s ability=%s action=%s mode=%s", state["session_id"], state.get("question_count", 0) + 1, ability, state.get("next_action"), mode)
    return {"current_question": question, "messages": messages, "question_count": state.get("question_count", 0) + 1, "ability_question_counts": counts, "agent_mode": "llm" if state.get("agent_mode") == "llm" and mode == "llm" else mode}


async def analyze_node(state: InterviewState) -> dict:
    answer = next((item.get("content", "") for item in reversed(state.get("messages", [])) if item.get("role") == "user"), "")

    def fallback() -> dict:
        keywords = _technical_points(answer)
        numbers = re.findall(r"\d+(?:\.\d+)?%?", answer)
        if len(answer) < 15:
            quality = "needs_clarification"
        elif keywords or len(answer) >= 40:
            quality = "good"
        else:
            quality = "normal"
        project = _detect_project(state, answer)
        ability = _detect_ability(answer, keywords, state["current_ability"])
        return {
            "quality": quality, "ability": ability, "project_detected": project,
            "ability_detected": ability, "technical_points": keywords,
            "confidence": 88 if keywords and project else 75 if keywords else 60,
            "relevance": 85 if keywords else 65, "completeness": min(95, 45 + len(answer) // 2),
            "depth": 82 if keywords else 55, "quantification": 85 if numbers else 35,
            "authenticity": 75, "logic": 78 if len(answer) >= 20 else 55,
            "evidence": answer[:220] if answer else "",
            "missing": [] if numbers and len(answer) > 40 else ["缺少实现细节或量化结果"],
            "keywords": keywords,
        }

    payload, mode = await _structured_call(build_analyze_prompt(state, answer), fallback)
    analysis = {**fallback(), **payload}
    llm_points = analysis.get("technical_points", [])
    llm_keywords = analysis.get("keywords", [])
    if isinstance(llm_points, str):
        llm_points = [llm_points]
    if isinstance(llm_keywords, str):
        llm_keywords = [llm_keywords]
    analysis["technical_points"] = list(dict.fromkeys([*_technical_points(answer), *llm_points, *llm_keywords]))
    analysis["keywords"] = llm_keywords
    analysis["project_detected"] = _detect_project(state, answer) or str(analysis.get("project_detected", ""))
    analysis["ability_detected"] = _detect_ability(answer, analysis["technical_points"], str(analysis.get("ability_detected") or analysis.get("ability") or state["current_ability"]))
    analysis["ability"] = analysis["ability_detected"]
    analysis["confidence"] = max(0, min(100, int(analysis.get("confidence", 60))))
    evidence = analysis.get("evidence", "")
    if isinstance(evidence, list):
        evidence = evidence[0] if evidence else ""
    analysis["evidence"] = str(evidence or answer[:220])
    project_context, project_count = _merge_project_context(state, answer, analysis)
    analysis["project_detected"] = project_context.get("project_name", analysis["project_detected"])
    evidence_items = list(state.get("evidences", []))
    if analysis["evidence"]:
        evidence_items.append({"ability": analysis["ability_detected"], "content": analysis["evidence"], "question": state.get("current_question", ""), "project": project_context.get("project_name", ""), "technical_points": analysis["technical_points"], "confidence": analysis["confidence"], "missing": analysis.get("missing", [])})
    logger.info("[%s] analysis quality=%s ability=%s keywords=%s mode=%s", state["session_id"], analysis.get("quality"), analysis.get("ability"), analysis.get("keywords"), mode)
    return {"answer_analysis": analysis, "evidences": evidence_items, "current_project_context": project_context, "project_question_count": project_count, "agent_mode": "llm" if state.get("agent_mode") == "llm" and mode == "llm" else mode}


async def decision_node(state: InterviewState) -> dict:
    analysis = state.get("answer_analysis", {})
    recognized = analysis.get("ability_detected") or analysis.get("ability")
    current = state["current_ability"]
    pending = list(state.get("pending_abilities", []))
    covered = list(state.get("covered_abilities", []))
    detected_switch = bool(recognized and recognized != current)

    def fallback() -> dict:
        count = state.get("ability_question_counts", {}).get(current, 0)
        if state.get("question_count", 0) >= state.get("total_questions", 10):
            action = "finish"
        elif detected_switch:
            action = "deep_question"
        elif analysis.get("quality") == "needs_clarification" and count < 2:
            action = "clarify"
        elif analysis.get("keywords") and count < 2:
            action = "deep_question"
        elif pending:
            action = "switch_ability"
        else:
            action = "finish"
        return {"action": action, "reason": "根据回答完整性、技术关键词和能力覆盖自动决策"}

    payload, mode = await _structured_call(build_decision_prompt(state), fallback)
    action = payload.get("action")
    if action not in {"deep_question", "clarify", "switch_ability", "finish"}:
        action = fallback()["action"]
    count = state.get("ability_question_counts", {}).get(current, 0)
    if state.get("question_count", 0) >= state.get("total_questions", 10):
        action = "finish"
    elif detected_switch:
        if current not in covered:
            covered.append(current)
        current = recognized
        if recognized in pending:
            pending.remove(recognized)
        action = "deep_question"
    elif action in {"deep_question", "clarify"} and count >= 2:
        action = "switch_ability" if pending else "finish"
    elif action == "finish" and pending:
        action = "switch_ability"
    if action == "switch_ability":
        if current not in covered:
            covered.append(current)
        if pending:
            current = pending.pop(0)
        else:
            action = "finish"
    if action == "finish" and current not in covered:
        covered.append(current)
    logger.info("[%s] decision=%s current=%s pending=%s mode=%s", state["session_id"], action, current, pending, mode)
    return {"next_action": action, "decision_reason": payload.get("reason", fallback()["reason"]), "current_ability": current, "current_stage": _stage_for_ability(state, current), "covered_abilities": covered, "pending_abilities": pending, "should_finish": action == "finish", "agent_mode": "llm" if state.get("agent_mode") == "llm" and mode == "llm" else mode}


async def report_node(state: InterviewState) -> dict:
    def fallback() -> dict:
        return {"evidence_count": len(state.get("evidences", [])), "covered_abilities": state.get("covered_abilities", []), "scoring_basis": ["回答相关性与完整性", "技术深度与量化证据", "岗位能力覆盖程度"], "summary": "面试已完成，能力证据已提交评估报告模块。"}
    payload, mode = await _structured_call(build_report_prompt(state), fallback)
    logger.info("[%s] report evidences=%s mode=%s", state["session_id"], len(state.get("evidences", [])), mode)
    return {"report_data": {**fallback(), **payload}, "should_finish": True, "agent_mode": "llm" if state.get("agent_mode") == "llm" and mode == "llm" else mode}
