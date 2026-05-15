"""Load pickle artifacts and run inference."""

from __future__ import annotations

import logging
import pickle
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from churn_api.features import engineered_feature_frame, request_to_single_row_df
from churn_api.schemas import ChurnPredictRequest, ChurnPredictResponse

logger = logging.getLogger(__name__)

# ── Hardcoded artifact paths ───────────────────────────────────────────────────
PREPROCESSOR_PATH = Path("artifacts/preprocessor.pkl")
MODEL_PATH        = Path("artifacts/model.pkl")
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class ChurnPredictor:
    """Holds fitted preprocessor + classifier loaded from pickle files."""

    preprocessor: Any
    classifier: Any
    # Keep these fields so /health and predict responses stay unchanged
    run_id: str = "local"
    model_version: str = "local"
    registered_model_name: str = "local"

    @classmethod
    def from_pickle(
        cls,
        preprocessor_path: Path = PREPROCESSOR_PATH,
        model_path: Path = MODEL_PATH,
    ) -> "ChurnPredictor":
        """Load preprocessor and classifier from pickle files."""
        t0 = time.perf_counter()

        preprocessor_path = Path(preprocessor_path).expanduser().resolve()
        model_path = Path(model_path).expanduser().resolve()

        if not preprocessor_path.is_file():
            raise FileNotFoundError(f"Preprocessor pickle not found: {preprocessor_path}")
        if not model_path.is_file():
            raise FileNotFoundError(f"Model pickle not found: {model_path}")

        logger.info("Loading preprocessor from %s", preprocessor_path)
        with open(preprocessor_path, "rb") as f:
            preprocessor = pickle.load(f)

        logger.info("Loading classifier from %s", model_path)
        with open(model_path, "rb") as f:
            classifier = pickle.load(f)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info("Loaded pickle artifacts duration_ms=%.1f", elapsed_ms)

        return cls(preprocessor=preprocessor, classifier=classifier)

    # Keep from_settings as a thin shim so main.py needs no changes
    @classmethod
    def from_settings(cls, settings: Any) -> "ChurnPredictor":
        return cls.from_pickle()

    def predict(self, payload: ChurnPredictRequest) -> ChurnPredictResponse:
        raw_df = request_to_single_row_df(payload)
        logger.info(
            "predict.start geography=%s gender=%s age=%s",
            payload.Geography,
            payload.Gender,
            payload.Age,
        )
        t0 = time.perf_counter()

        X = engineered_feature_frame(self.preprocessor, raw_df)
        y_hat = self.classifier.predict(X)
        proba_row = self.classifier.predict_proba(X)[0]

        classes = getattr(self.classifier, "classes_", None)
        if classes is not None and 1 in classes:
            churn_idx = list(classes).index(1)
        else:
            churn_idx = int(proba_row.argmax())

        probability_churn = float(proba_row[churn_idx])
        prediction = int(y_hat[0])
        elapsed_ms = (time.perf_counter() - t0) * 1000

        logger.info(
            "predict.end prediction=%s p_churn=%.4f duration_ms=%.2f",
            prediction,
            probability_churn,
            elapsed_ms,
        )
        return ChurnPredictResponse(
            prediction=prediction,
            probability_churn=probability_churn,
            mlflow_run_id=self.run_id,
            model_version=self.model_version,
            model_name=self.registered_model_name,
        )