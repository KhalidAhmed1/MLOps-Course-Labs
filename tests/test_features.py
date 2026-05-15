"""Unit tests for pure feature-engineering helpers."""

import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from churn_api.features import engineered_feature_frame, request_to_single_row_df
from churn_api.schemas import ChurnPredictRequest


def test_request_to_single_row_df_preserves_columns():
    payload = ChurnPredictRequest(
        CreditScore=650,
        Geography="France",
        Gender="Female",
        Age=42,
        Tenure=3,
        Balance=120_000.0,
        NumOfProducts=2,
        HasCrCard=1,
        IsActiveMember=1,
        EstimatedSalary=80_000.0,
    )
    df = request_to_single_row_df(payload)
    assert df.shape == (1, 10)
    assert list(df.columns) == list(ChurnPredictRequest.model_fields.keys())


@pytest.fixture()
def fitted_preprocessor() -> ColumnTransformer:
    raw = pd.DataFrame(
        {
            "CreditScore": [600, 700],
            "Geography": ["France", "Spain"],
            "Gender": ["Male", "Female"],
            "Age": [30, 40],
            "Tenure": [1, 5],
            "Balance": [0.0, 10_000.0],
            "NumOfProducts": [1, 2],
            "HasCrCard": [1, 0],
            "IsActiveMember": [1, 0],
            "EstimatedSalary": [50_000.0, 60_000.0],
        }
    )
    cat_cols = ["Geography", "Gender"]
    num_cols = [c for c in raw.columns if c not in cat_cols]
    pre = ColumnTransformer(
        [
            ("num", StandardScaler(), num_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
        ]
    )
    pre.fit(raw)
    return pre


def test_engineered_feature_frame_matches_training_pattern(fitted_preprocessor):
    raw_df = pd.DataFrame(
        {
            "CreditScore": [650],
            "Geography": ["France"],
            "Gender": ["Female"],
            "Age": [42],
            "Tenure": [3],
            "Balance": [100.0],
            "NumOfProducts": [2],
            "HasCrCard": [1],
            "IsActiveMember": [1],
            "EstimatedSalary": [55_000.0],
        }
    )
    out = engineered_feature_frame(fitted_preprocessor, raw_df)
    assert out.shape[0] == 1
    assert out.shape[1] == len(fitted_preprocessor.get_feature_names_out())
    assert not np.isnan(out.to_numpy()).any()
