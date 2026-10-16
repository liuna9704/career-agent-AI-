from pydantic import BaseModel, Field


class JobItem(BaseModel):
    key: str
    name: str
    description: str


class CompetencyItem(BaseModel):
    name: str
    summary: str


class JobCompetencies(BaseModel):
    job: str
    competencies: list[CompetencyItem]
    ready: bool = True


class CompetencyModelItem(BaseModel):
    name: str
    description: str
    indicators: list[str]
    interview_points: list[str]
    score_rule: str


class JobCompetencyModel(BaseModel):
    job: str
    competencies: list[CompetencyModelItem]


class KnowledgeSearchRequest(BaseModel):
    job: str
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=3, ge=1, le=10)


class KnowledgeSearchResult(BaseModel):
    job: str
    ability: str
    content: str
    score: float
    source: str


class KnowledgeSearchData(BaseModel):
    query: str
    mode: str
    results: list[KnowledgeSearchResult]
