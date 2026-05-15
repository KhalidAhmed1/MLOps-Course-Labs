"""Pure helpers to turn API payloads into model-ready tabular data."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from churn_api.schemas import ChurnPredictRequest

logger = logging.getLogger(__name__)


def request_to_single_row_df(payload: ChurnPredictRequest) -> pd.DataFrame:
    """
    Build a one-row DataFrame with the same column order as training features
    (before ``ColumnTransformer``).
    """
    row: dict[str, Any] = payload.model_dump()
    df = pd.DataFrame([row])
    logger.debug("Built feature frame columns=%s", list(df.columns))
    return df


def engineered_feature_frame(preprocessor: Any, raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the fitted ``ColumnTransformer`` and restore column names expected
    by classifiers trained in ``train.py``.
    """
    transformed = preprocessor.transform(raw_df)
    names = preprocessor.get_feature_names_out()
    out = pd.DataFrame(transformed, columns=names)
    logger.debug("Engineered shape=%s", out.shape)
    return out
