from fastapi import APIRouter, HTTPException, status

from app.schemas.common import ApiResponse
from app.schemas.report import AssessmentReport
from app.services.report_service import report_service

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/{session_id}", response_model=ApiResponse[AssessmentReport])
async def get_report(session_id: str) -> ApiResponse[AssessmentReport]:
    report = report_service.generate(session_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="面试会话不存在，无法生成评估报告",
        )
    return ApiResponse(code=200, message="报告生成成功", data=report)

