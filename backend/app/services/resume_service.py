import json
import os
import re
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import ValidationError

from app.core.llm import LLMError
from app.prompts.resume_prompt import build_resume_prompt
from app.schemas.resume import ProjectItem, ResumeProfile
from app.services.llm_service import llm_service
from app.services.resume_parser import ResumeParseError, extract_text


class ResumeService:
    def __init__(self) -> None:
        self.latest_profile: ResumeProfile | None = None

    async def parse(self, filename: str, content: bytes) -> ResumeProfile:
        suffix = Path(filename).suffix.lower()
        with TemporaryDirectory(prefix="career_resume_") as temp_dir:
            path = Path(temp_dir) / f"resume{suffix}"
            path.write_bytes(content)
            resume_text = extract_text(path)

        try:
            raw_response = await llm_service.chat(build_resume_prompt(resume_text))
            payload = self._parse_json(raw_response)
            profile = ResumeProfile.model_validate(payload)
            profile.analysis_mode = "llm"
            self.latest_profile = profile
            return profile
        except (LLMError, ValidationError, json.JSONDecodeError, ValueError) as exc:
            if not self._fallback_enabled():
                raise ResumeParseError("AI简历分析失败，请检查模型配置或稍后重试") from exc
            profile = self._fallback_profile(resume_text, str(exc))
            self.latest_profile = profile
            return profile

    @staticmethod
    def _parse_json(raw_response: str) -> dict:
        cleaned = raw_response.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end < start:
            raise json.JSONDecodeError("未找到JSON对象", cleaned, 0)
        return json.loads(cleaned[start : end + 1])

    @staticmethod
    def _fallback_enabled() -> bool:
        return os.getenv("LLM_MOCK_FALLBACK", "true").lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _fallback_profile(text: str, reason: str) -> ResumeProfile:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        skills_catalog = ["Java", "Spring Boot", "MySQL", "Redis", "Docker", "Python", "PyTorch", "Vue", "Linux"]
        skills = [skill for skill in skills_catalog if skill.lower() in text.lower()]
        name = next((line for line in lines[:6] if 2 <= len(line) <= 12 and not re.search(r"[:：@\d]", line)), "未知")
        education = next((line for line in lines if any(word in line for word in ["本科", "硕士", "博士", "大专"])), "未知")
        major = next((line for line in lines if "专业" in line or "计算机" in line), "未知")
        target_job = next((job for job in ["Java开发工程师", "AI算法工程师", "产品经理"] if job in text), "未知")
        project_line = next((line for line in lines if "项目" in line and len(line) <= 40), "未知")
        responsibility = next((line for line in lines if any(word in line for word in ["负责", "参与", "主导"])), "未知")
        project = ProjectItem(
            name=project_line,
            technology="、".join(skills) if skills else "未知",
            responsibility=responsibility,
            result="未知",
        )
        return ResumeProfile(
            name=name,
            education=education,
            major=major,
            target_job=target_job,
            skills=skills,
            projects=[] if project_line == "未知" else [project],
            advantages=["具备相关技术与项目经历"] if skills else [],
            weaknesses=["当前为本地降级解析，完整能力需要面试验证"],
            potential_questions=["请说明项目中的个人职责和量化结果"],
            analysis_mode="fallback",
            warning=f"大模型暂不可用，已使用本地解析：{reason}",
        )


resume_service = ResumeService()
