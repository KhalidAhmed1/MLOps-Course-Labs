import pytest
from fastapi.testclient import TestClient

from churn_api.main import create_app
from churn_api.schemas import ChurnPredictRequest, ChurnPredictResponse
from churn_api.telemetry import reset_hyperdx_state


@pytest.fixture(autouse=True)
def _isolate_hyperdx_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HYPERDX_API_KEY", raising=False)
    monkeypatch.delenv("CHURN_API_DISABLE_HYPERDX", raising=False)
    reset_hyperdx_state()


class StubPredictor:
    """Deterministic predictor for API tests (no MLflow)."""

    run_id = "stub-run-id"
    model_version = "stub-version"
    registered_model_name = "Stub_Model"

    def predict(self, payload: ChurnPredictRequest) -> ChurnPredictResponse:
        _ = payload
        return ChurnPredictResponse(
            prediction=0,
            probability_churn=0.42,
            mlflow_run_id=self.run_id,
            model_version=self.model_version,
            model_name=self.registered_model_name,
        )


@pytest.fixture()
def client() -> TestClient:
    app = create_app(predictor=StubPredictor())
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def sample_request_body() -> dict:
    return {
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
