from typing import Literal

from pydantic import BaseModel, Field


class InterviewStartRequest(BaseModel):
    job: str = Field(min_length=2, max_length=50)


class InterviewAnalysis(BaseModel):
    quality: Literal["good", "normal", "needs_clarification"]
    keywords: list[str]
    project_detected: str = ""
    ability_detected: str = ""
    technical_points: list[str] = Field(default_factory=list)
    evidence: str = ""
    confidence: int = Field(default=0, ge=0, le=100)


class AgentTraceItem(BaseModel):
    label: str
    status: Literal["done", "active", "info"] = "done"


class InterviewStartData(BaseModel):
    session_id: str
    job: str
    stage: str
    progress: int
    total: int
    ability: str
    question: str
    ability_coverage: dict[str, str]
    agent_trace: list[AgentTraceItem] = Field(default_factory=list)
    evidences: list[str] = Field(default_factory=list)
    rag_enhanced: bool = True
    agent_mode: str = "fallback"
    current_project_context: dict = Field(default_factory=dict)
    technical_points: list[str] = Field(default_factory=list)


class InterviewChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    answer: str = Field(min_length=1, max_length=5000)


class InterviewChatData(BaseModel):
    stage: str
    progress: int
    total: int
    ability: str
    analysis: InterviewAnalysis
    question: str
    ability_coverage: dict[str, str]
    completed: bool = False
    agent_trace: list[AgentTraceItem] = Field(default_factory=list)
    evidences: list[str] = Field(default_factory=list)
    rag_enhanced: bool = True
    agent_mode: str = "fallback"
    current_project_context: dict = Field(default_factory=dict)
    technical_points: list[str] = Field(default_factory=list)
