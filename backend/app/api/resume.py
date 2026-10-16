import json
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.common import ApiResponse
from app.schemas.resume import ResumeProfile
from app.services.resume_parser import ResumeParseError
from app.services.resume_service import resume_service

router = APIRouter(prefix="/resume", tags=["resume"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024
DEMO_ROOT = Path(__file__).resolve().parents[3] / "demo_data" / "examples"


@router.post("/demo/{job}", response_model=ApiResponse[ResumeProfile])
async def load_demo_resume(job: str) -> ApiResponse[ResumeProfile]:
    mapping = {"Java开发工程师": "java_engineer.json", "AI算法工程师": "ai_engineer.json", "产品经理": "product_manager.json"}
    filename = mapping.get(job)
    if not filename:
        raise HTTPException(status_code=404, detail="暂无该岗位演示数据")
    profile = ResumeProfile.model_validate(json.loads((DEMO_ROOT / filename).read_text(encoding="utf-8")))
    resume_service.latest_profile = profile
    return ApiResponse(code=200, message="演示简历加载成功", data=profile)


@router.post("/upload", response_model=ApiResponse[ResumeProfile])
async def upload_resume(file: UploadFile = File(...)) -> ApiResponse[ResumeProfile]:
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 PDF 或 DOCX 格式的简历",
        )

    content = await file.read(MAX_FILE_SIZE + 1)
    await file.close()
    if not content:
        raise HTTPException(status_code=400, detail="上传文件不能为空")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="简历文件不能超过 10MB")

    try:
        profile = await resume_service.parse(file.filename or "resume", content)
    except ResumeParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    message = "AI解析成功" if profile.analysis_mode == "llm" else "文本提取成功，已使用本地降级分析"
    return ApiResponse(code=200, message=message, data=profile)
