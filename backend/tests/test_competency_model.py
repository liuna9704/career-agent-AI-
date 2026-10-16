from fastapi.testclient import TestClient

from app.main import app
from app.services.rag_service import rag_service


def test_all_jobs_have_self_built_competency_models():
    for job in ("AI算法工程师", "Java开发工程师", "产品经理"):
        model = rag_service.get_competency_model(job)
        assert model["job"] == job
        assert len(model["competencies"]) >= 5
        for item in model["competencies"]:
            assert item["description"]
            assert item["indicators"]
            assert item["interview_points"]
            assert item["score_rule"]


def test_competency_model_api():
    response = TestClient(app).get("/api/jobs/AI算法工程师/competency-model")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    assert any(item["name"] == "大模型应用能力" for item in body["data"]["competencies"])
