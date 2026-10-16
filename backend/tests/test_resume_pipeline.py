import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.llm_service import llm_service
from app.services.resume_parser import extract_text
from app.services.resume_service import resume_service

FIXTURES = Path(__file__).parent / "fixtures"


async def run() -> None:
    pdf_path = FIXTURES / "test_resume.pdf"
    docx_path = FIXTURES / "test_resume.docx"
    pdf_text = extract_text(pdf_path)
    docx_text = extract_text(docx_path)
    assert "Spring Boot" in pdf_text and "Redis" in docx_text

    fallback = await resume_service.parse(pdf_path.name, pdf_path.read_bytes())
    assert fallback.analysis_mode == "fallback"
    assert "Java" in fallback.skills

    original_chat = llm_service.chat

    async def fake_chat(prompt: str) -> str:
        assert "Intelligent Recruitment System" in prompt
        return json.dumps({
            "name": "Zhang San",
            "education": "Bachelor",
            "major": "Computer Science",
            "target_job": "Java Developer",
            "skills": ["Java", "Spring Boot", "MySQL", "Redis", "Docker"],
            "projects": [{
                "name": "Intelligent Recruitment System",
                "technology": "Spring Boot, MySQL, Redis, Docker",
                "responsibility": "Designed backend APIs and optimized database queries.",
                "result": "Reduced average API latency by 35 percent."
            }],
            "advantages": ["Backend engineering experience"],
            "weaknesses": ["Distributed systems evidence is limited"],
            "potential_questions": ["How was the latency reduction measured?"]
        })

    llm_service.chat = fake_chat
    try:
        llm_profile = await resume_service.parse(docx_path.name, docx_path.read_bytes())
    finally:
        llm_service.chat = original_chat
    assert llm_profile.analysis_mode == "llm"
    assert llm_profile.projects[0].result.startswith("Reduced")
    print("resume pipeline passed", len(pdf_text), len(docx_text), llm_profile.name)


if __name__ == "__main__":
    asyncio.run(run())
