"""HTTP-level tests for the FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from churn_api.main import create_app
from churn_api.schemas import ChurnPredictRequest, ChurnPredictResponse
from tests.conftest import StubPredictor


def test_home_endpoint_returns_service_metadata(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "Bank churn prediction API"
    assert "/health" in body["health"]
    assert "/predict" in body["predict"]


def test_health_endpoint_reports_model_loaded(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True
    # model_version is still present; mlflow_run_id was removed (pickle-based loading)
    assert data["model_version"] == "stub-version"


def test_predict_endpoint_success(client: TestClient, sample_request_body: dict):
    response = client.post("/predict", json=sample_request_body)
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] == 0
    assert data["probability_churn"] == pytest.approx(0.42)
    assert data["mlflow_run_id"] == "stub-run-id"


def test_predict_endpoint_validation_error(client: TestClient, sample_request_body: dict):
    bad = dict(sample_request_body)
    bad["Geography"] = "Atlantis"
    response = client.post("/predict", json=bad)
    assert response.status_code == 422


def test_predict_endpoint_internal_error():
    class BoomPredictor(StubPredictor):
        def predict(self, payload: ChurnPredictRequest) -> ChurnPredictResponse:
            raise RuntimeError("boom")

    app = create_app(predictor=BoomPredictor())
    with TestClient(app, raise_server_exceptions=False) as client:
        body = {
            "CreditScore": 650,
            "Geography": "France",
            "Gender": "Female",
            "Age": 42,
            "Tenure": 3,
            "Balance": 120_000.0,
            "NumOfProducts": 2,
            "HasCrCard": 1,
            "IsActiveMember": 1,
            "EstimatedSalary": 80_000.0,
        }
        response = client.post("/predict", json=body)
    assert response.status_code == 500
    assert response.json()["detail"] == "Prediction failed"


def test_health_degraded_when_model_missing():
    app = create_app(predictor=StubPredictor())
    with TestClient(app) as client:
        app.state.predictor = None
        response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["model_loaded"] is False