import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.interview_service import InterviewService
from app.services.llm_service import llm_service


async def fake_chat(prompt: str) -> str:
    if "规划一场岗位面试" in prompt:
        return json.dumps({"plan": [
            {"stage": "基础能力", "ability": "Java基础", "reason": "基础验证"},
            {"stage": "项目深入追问", "ability": "Spring Boot", "reason": "简历技能"},
            {"stage": "业务场景", "ability": "Redis", "reason": "缓存能力"},
        ]}, ensure_ascii=False)
    if "专业技术面试评估员" in prompt:
        ability = "Redis" if "Redis" in prompt.split("候选人回答：")[-1] else "Spring Boot"
        return json.dumps({"quality": "good", "ability": ability, "relevance": 90, "completeness": 80, "depth": 82, "quantification": 60, "authenticity": 75, "logic": 85, "evidence": [f"回答体现{ability}实践"], "missing": ["需要更多量化指标"], "keywords": [ability]}, ensure_ascii=False)
    if "面试流程决策器" in prompt:
        return json.dumps({"action": "deep_question", "reason": "存在可深入验证的技术细节"}, ensure_ascii=False)
    if "生成一个且仅一个针对性面试问题" in prompt:
        if "Redis" in prompt:
            question = "你在项目中如何保证Redis缓存与数据库的一致性？"
        elif "Spring Boot" in prompt:
            question = "为什么选择Spring Boot，并如何设计事务边界？"
        else:
            question = "请结合项目说明Java并发设计与验证结果。"
        return json.dumps({"question": question}, ensure_ascii=False)
    return json.dumps({"evidence_count": 2, "covered_abilities": ["Java基础"], "scoring_basis": ["技术深度"], "summary": "测试完成"}, ensure_ascii=False)


async def run() -> None:
    original = llm_service.chat
    llm_service.chat = fake_chat
    try:
        service = InterviewService()
        started = await service.start("Java开发工程师")
        assert started.ability == "Java基础"
        spring = await service.chat(started.session_id, "我使用Spring Boot开发智能招聘系统并设计事务服务。")
        assert spring and spring.ability == "Spring Boot" and "事务" in spring.question
        redis = await service.chat(started.session_id, "我使用Redis缓存热点数据。")
        assert redis and redis.ability == "Redis" and "一致性" in redis.question
        state = service.sessions[started.session_id].agent_state
        assert state["agent_mode"] == "llm"
        assert len(state["evidences"]) == 2
        print("langgraph llm path passed", started.session_id, spring.question, redis.question)
    finally:
        llm_service.chat = original


if __name__ == "__main__":
    asyncio.run(run())
