from fastapi import APIRouter, HTTPException

from app.schemas.common import ApiResponse
from app.schemas.knowledge import JobCompetencies, JobCompetencyModel, JobItem, KnowledgeSearchData, KnowledgeSearchRequest, KnowledgeSearchResult
from app.services.rag_service import JOB_CATALOG, rag_service

router = APIRouter(tags=["knowledge"])


@router.get("/jobs", response_model=ApiResponse[list[JobItem]])
async def get_jobs() -> ApiResponse[list[JobItem]]:
    jobs = [JobItem(key=key, **value) for key, value in JOB_CATALOG.items()]
    return ApiResponse(code=200, message="岗位列表获取成功", data=jobs)


@router.get("/jobs/{job}/competencies", response_model=ApiResponse[JobCompetencies])
async def get_job_competencies(job: str) -> ApiResponse[JobCompetencies]:
    try:
        data = JobCompetencies.model_validate(rag_service.get_competencies(job))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="暂不支持该岗位") from exc
    return ApiResponse(code=200, message="岗位能力模型获取成功", data=data)


@router.get("/jobs/{job}/competency-model", response_model=ApiResponse[JobCompetencyModel])
async def get_job_competency_model(job: str) -> ApiResponse[JobCompetencyModel]:
    try:
        data = JobCompetencyModel.model_validate(rag_service.get_competency_model(job))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="暂不支持该岗位") from exc
    return ApiResponse(code=200, message="岗位胜任力模型获取成功", data=data)


@router.post("/knowledge/search", response_model=ApiResponse[KnowledgeSearchData])
async def search_knowledge(payload: KnowledgeSearchRequest) -> ApiResponse[KnowledgeSearchData]:
    try:
        results = await rag_service.search(payload.job, payload.query, payload.top_k)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="暂不支持该岗位") from exc
    data = KnowledgeSearchData(query=payload.query, mode=rag_service.client.mode, results=[KnowledgeSearchResult(job=item["job"], ability=item["ability"], content=item["content"], score=item["score"], source=item["source"]) for item in results])
    return ApiResponse(code=200, message="岗位知识检索成功", data=data)
