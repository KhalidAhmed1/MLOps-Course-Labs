"""Request / response models for the API."""

from typing import Literal

from pydantic import BaseModel, Field


class ChurnPredictRequest(BaseModel):
    """Raw customer features (same columns as training, excluding ``Exited``)."""

    CreditScore: int = Field(..., ge=300, le=900)
    Geography: Literal["France", "Spain", "Germany"]
    Gender: Literal["Male", "Female"]
    Age: int = Field(..., ge=18, le=100)
    Tenure: int = Field(..., ge=0, le=10)
    Balance: float = Field(..., ge=0)
    NumOfProducts: int = Field(..., ge=1, le=4)
    HasCrCard: int = Field(..., ge=0, le=1)
    IsActiveMember: int = Field(..., ge=0, le=1)
    EstimatedSalary: float = Field(..., ge=0)


class ChurnPredictResponse(BaseModel):
    prediction: int = Field(..., description="0 = stay, 1 = churn")
    probability_churn: float = Field(..., ge=0.0, le=1.0)
    mlflow_run_id: str
    model_version: str
    model_name: str
