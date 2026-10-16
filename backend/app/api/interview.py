from fastapi import APIRouter, HTTPException, status

from app.schemas.common import ApiResponse
from app.schemas.interview import (
    InterviewChatData,
    InterviewChatRequest,
    InterviewStartData,
    InterviewStartRequest,
)
from app.services.interview_service import interview_service

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/start", response_model=ApiResponse[InterviewStartData])
async def start_interview(payload: InterviewStartRequest) -> ApiResponse[InterviewStartData]:
    data = await interview_service.start(payload.job)
    return ApiResponse(code=200, message="面试创建成功", data=data)


@router.post("/chat", response_model=ApiResponse[InterviewChatData])
async def chat(payload: InterviewChatRequest) -> ApiResponse[InterviewChatData]:
    data = await interview_service.chat(payload.session_id, payload.answer.strip())
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="面试会话不存在或已失效",
        )
    return ApiResponse(code=200, message="回答分析完成", data=data)
