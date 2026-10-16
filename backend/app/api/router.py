from fastapi import APIRouter

from app.api.resume import router as resume_router
from app.api.interview import router as interview_router
from app.api.report import router as report_router
from app.api.knowledge import router as knowledge_router

router = APIRouter()
router.include_router(resume_router)
router.include_router(interview_router)
router.include_router(report_router)
router.include_router(knowledge_router)


@router.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "career-agent-api"}
