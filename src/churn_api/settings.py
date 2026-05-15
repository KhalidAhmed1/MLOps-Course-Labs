"""Runtime configuration (env + defaults)."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_tracking_uri() -> str:
    repo_root = Path(__file__).resolve().parent.parent.parent
    return (repo_root / "mlruns").as_uri()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CHURN_API_",
        env_file=".env",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    tracking_uri: str = Field(default_factory=_default_tracking_uri)
    registered_model_name: str = "Bank_Churn_Classifier"
    champion_alias: str = Field(
        default="champion",
        description="MLflow registered model alias pointing at the champion version.",
    )
    model_artifacts_dir: str | None = Field(
        default=None,
        description=(
            "If set, load sklearn MLflow model directories from "
            "{dir}/preprocessor and {dir}/model (bind-mount at runtime). "
            "When unset, the registry + tracking_uri path is used instead."
        ),
    )
    bundle_run_id: str = Field(
        default="mounted",
        description="mlflow_run_id label in /predict when using model_artifacts_dir.",
    )
    bundle_model_version: str = Field(
        default="0",
        description="model_version label when using model_artifacts_dir.",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
