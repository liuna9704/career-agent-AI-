from typing import Literal

from pydantic import BaseModel, Field


class ProjectItem(BaseModel):
    name: str = "未知"
    technology: str = "未知"
    responsibility: str = "未知"
    result: str = "未知"


class ResumeProfile(BaseModel):
    name: str = "未知"
    education: str = "未知"
    major: str = "未知"
    target_job: str = "未知"
    skills: list[str] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    advantages: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    potential_questions: list[str] = Field(default_factory=list)
    analysis_mode: Literal["llm", "fallback"] = "llm"
    warning: str | None = None

