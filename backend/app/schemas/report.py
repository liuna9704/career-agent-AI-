from pydantic import BaseModel, Field


class ReportCandidate(BaseModel):
    name: str
    job: str


class ReportSummary(BaseModel):
    score: int
    match_rate: int
    level: str
    confidence: str


class RadarItem(BaseModel):
    name: str
    score: int


class AbilityAssessment(BaseModel):
    name: str
    score: int
    evidence: str
    problem: str
    evaluation_basis: list[str] = Field(default_factory=list)


class EvidenceTimelineItem(BaseModel):
    question: str
    answer: str
    judgment: str
    ability: str
    project: str = ""


class AbilityVerification(BaseModel):
    claim: str
    verified: str
    confidence: str


class CareerAdvice(BaseModel):
    learning_directions: list[str]
    recommended_project: str
    roadmap: list[str]


class AssessmentReport(BaseModel):
    candidate: ReportCandidate
    summary: ReportSummary
    radar: list[RadarItem]
    abilities: list[AbilityAssessment]
    advantages: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    evidence_timeline: list[EvidenceTimelineItem] = Field(default_factory=list)
    verifications: list[AbilityVerification] = Field(default_factory=list)
    career_advice: CareerAdvice
