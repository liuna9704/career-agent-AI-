from collections import defaultdict

from app.schemas.report import (
    AbilityAssessment, AbilityVerification, AssessmentReport, CareerAdvice,
    EvidenceTimelineItem, RadarItem, ReportCandidate, ReportSummary,
)
from app.services.interview_service import InterviewSession, interview_service


class ReportService:
    def generate(self, session_id: str) -> AssessmentReport | None:
        session = interview_service.sessions.get(session_id)
        return self._evidence_report(session) if session else None

    @staticmethod
    def _evidence_report(session: InterviewSession) -> AssessmentReport:
        state = session.agent_state or {}
        evidences = state.get("evidences", [])
        grouped: dict[str, list[dict]] = defaultdict(list)
        for item in evidences:
            grouped[item.get("ability") or "综合岗位能力"].append(item)

        abilities: list[AbilityAssessment] = []
        radar: list[RadarItem] = []
        weaknesses: list[str] = []
        for ability, items in grouped.items():
            confidence_values = [int(item.get("confidence", 65)) for item in items]
            score = max(55, min(95, round(sum(confidence_values) / len(confidence_values))))
            evidence_text = "；".join(item.get("content", "") for item in items[-2:] if item.get("content"))
            missing = [str(x) for item in items for x in item.get("missing", []) if x]
            problem = missing[-1] if missing else "当前证据已验证基础实践，复杂场景仍可继续考察"
            technical_points = list(dict.fromkeys(point for item in items for point in item.get("technical_points", [])))
            basis = [f"✓ 回答中可核验：{point}" for point in technical_points[:5]] or [f"✓ 能够围绕实际问题说明{ability}相关实践"]
            abilities.append(AbilityAssessment(name=ability, score=score, evidence=evidence_text or "已形成面试能力证据", problem=problem, evaluation_basis=basis))
            radar.append(RadarItem(name=ability, score=score))
            if missing and missing[-1] not in weaknesses:
                weaknesses.append(missing[-1])

        # 未覆盖维度也进入报告，明确展示自建模型的完整评估边界。
        existing = {item.name for item in abilities}
        for model_item in state.get("competency_model", []):
            name = model_item.get("name", "")
            if name and name not in existing:
                abilities.append(AbilityAssessment(name=name, score=55, evidence="本轮尚未收集到充分能力证据", problem="需要按照胜任力模型继续验证", evaluation_basis=[f"○ 待验证指标：{indicator}" for indicator in model_item.get("indicators", [])[:3]]))
                radar.append(RadarItem(name=name, score=55))

        # 无有效回答时仍保证报告页面可展示，但不伪造具体技术能力。
        if not abilities:
            abilities = [AbilityAssessment(name="待验证岗位能力", score=60, evidence="当前面试证据不足", problem="建议完成更多面试问题", evaluation_basis=["○ 尚无可核验回答"])]
            radar = [RadarItem(name="待验证岗位能力", score=60)]

        score = round(sum(item.score for item in abilities) / len(abilities))
        match_rate = max(50, min(95, round(score * 0.9 + min(len(grouped), 5) * 2)))
        level = "强烈推荐" if score >= 90 else "推荐面试" if score >= 78 else "建议进一步考察"
        confidence = "较高" if len(evidences) >= 3 else "中等"

        timeline = [EvidenceTimelineItem(
            question=item.get("question", "面试问题"),
            answer=item.get("content", "候选人回答"),
            judgment=f"已形成{item.get('ability', '岗位')}证据（置信度{item.get('confidence', 60)}%）",
            ability=item.get("ability", "综合能力"),
            project=item.get("project", ""),
        ) for item in evidences[-8:]]

        candidate = state.get("candidate_profile", {})
        skills = candidate.get("skills", []) or []
        evidence_text = " ".join(
            [item.get("content", "") for item in evidences]
            + [" ".join(item.get("technical_points", [])) for item in evidences]
        ).lower()
        verifications = [AbilityVerification(
            claim=f"简历声明：熟悉{skill}",
            verified=f"面试验证：{'回答中出现了可核验的相关实践' if str(skill).lower() in evidence_text else '当前证据不足，仍需继续核验'}",
            confidence="较高" if str(skill).lower() in evidence_text else "中等",
        ) for skill in skills[:6]]

        advantages = [f"已验证{item.name}，证据置信度{item.score}%" for item in abilities if item.score >= 75][:4]
        if not advantages:
            advantages = ["能够围绕实际项目说明个人工作"]
        weaknesses = weaknesses[:4] or ["复杂场景和量化结果的证据仍需补充"]
        suggestions = [f"围绕“{item}”补充实现细节、方案权衡和量化结果" for item in weaknesses[:3]]
        directions = [item.name for item in sorted(abilities, key=lambda x: x.score)[:3]]
        project_name = state.get("current_project_context", {}).get("project_name") or "目标岗位综合实践项目"

        return AssessmentReport(
            candidate=ReportCandidate(name=candidate.get("name") or "候选人", job=session.job),
            summary=ReportSummary(score=score, match_rate=match_rate, level=level, confidence=confidence),
            radar=radar, abilities=abilities, advantages=advantages, weaknesses=weaknesses,
            suggestions=suggestions, evidence_timeline=timeline, verifications=verifications,
            career_advice=CareerAdvice(
                learning_directions=directions,
                recommended_project=f"继续完善“{project_name}”，补充性能、稳定性和可观测性验证",
                roadmap=["第1阶段：补齐薄弱能力的原理与方案对比", "第2阶段：在真实项目中完成专项实践", "第3阶段：压测复盘并沉淀量化证据"],
            ),
        )


report_service = ReportService()
