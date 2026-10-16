from typing import Any, Literal, TypedDict


class InterviewState(TypedDict, total=False):
    mode: Literal["start", "chat"]
    session_id: str
    candidate_profile: dict[str, Any]
    job: str
    job_context: list[dict[str, Any]]
    competency_model: list[dict[str, Any]]
    interview_plan: list[dict[str, str]]
    messages: list[dict[str, Any]]
    current_stage: str
    current_ability: str
    current_project_context: dict[str, Any]
    project_question_count: int
    current_question: str
    covered_abilities: list[str]
    pending_abilities: list[str]
    answer_analysis: dict[str, Any]
    evidences: list[dict[str, Any]]
    ability_question_counts: dict[str, int]
    question_count: int
    total_questions: int
    next_action: Literal["initial", "deep_question", "clarify", "switch_ability", "finish"]
    decision_reason: str
    should_finish: bool
    report_data: dict[str, Any]
    agent_mode: Literal["llm", "fallback"]
