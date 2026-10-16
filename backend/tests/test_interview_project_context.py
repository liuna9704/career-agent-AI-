import pytest

from app.agents import nodes


def base_state():
    return {
        "session_id": "test_context", "job": "Java开发工程师", "job_context": [],
        "candidate_profile": {"projects": [
            {"name": "智能巡检机器人管理平台"}, {"name": "AI智能面试平台"},
        ]},
        "messages": [], "current_stage": "项目深入追问", "current_ability": "Java基础",
        "current_question": "请介绍一个代表项目", "current_project_context": {},
        "project_question_count": 0, "evidences": [], "covered_abilities": [],
        "pending_abilities": ["Spring Boot"], "interview_plan": [], "ability_question_counts": {"Java基础": 1},
        "question_count": 1, "total_questions": 10, "next_action": "deep_question", "agent_mode": "fallback",
    }


@pytest.mark.asyncio
async def test_vue_project_is_locked_and_drives_frontend_question(monkeypatch):
    async def fail_llm(*_args, **_kwargs):
        raise RuntimeError("force deterministic fallback")
    monkeypatch.setattr(nodes.llm_service, "chat", fail_llm)
    monkeypatch.setattr(nodes.rag_service, "search", fail_llm)
    state = base_state()
    answer = "我负责开发智能巡检机器人管理平台，前端使用Vue3，实现机器人状态监控、地图展示和远程控制页面。"
    state["messages"] = [{"role": "user", "content": answer}]
    state.update(await nodes.analyze_node(state))
    assert state["current_project_context"]["project_name"] == "智能巡检机器人管理平台"
    assert state["answer_analysis"]["ability_detected"] == "前端工程能力"
    assert "Vue3" in state["answer_analysis"]["technical_points"]
    state.update(await nodes.decision_node(state))
    state.update(await nodes.question_node(state))
    assert "智能巡检机器人管理平台" in state["current_question"]
    assert any(word in state["current_question"] for word in ("组件", "状态", "地图", "接口"))
    assert "Node.js" not in state["current_question"] and "AI智能面试平台" not in state["current_question"]


@pytest.mark.asyncio
async def test_fastapi_llm_maps_to_ai_application_without_switching_project(monkeypatch):
    async def fail_llm(*_args, **_kwargs):
        raise RuntimeError("force deterministic fallback")
    monkeypatch.setattr(nodes.llm_service, "chat", fail_llm)
    monkeypatch.setattr(nodes.rag_service, "search", fail_llm)
    state = base_state()
    state["current_project_context"] = {"project_name": "智能巡检机器人管理平台", "technologies": ["Vue3"], "role": "前端开发"}
    state["project_question_count"] = 1
    answer = "项目后端使用FastAPI提供接口，并通过接口调用大模型完成智能分析。"
    state["messages"] = [{"role": "user", "content": answer}]
    state.update(await nodes.analyze_node(state))
    assert state["answer_analysis"]["ability_detected"] == "AI应用开发能力"
    assert {"FastAPI", "LLM API"}.issubset(state["answer_analysis"]["technical_points"])
    assert state["current_project_context"]["project_name"] == "智能巡检机器人管理平台"
