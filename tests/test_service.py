"""Unit tests for inference service (no HTTP stack)."""

import pickle

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from churn_api.features import engineered_feature_frame, request_to_single_row_df
from churn_api.schemas import ChurnPredictRequest
from churn_api.service import ChurnPredictor


def _toy_preprocessor_and_classifier():
    raw = pd.DataFrame(
        {
            "CreditScore": [600, 700, 650],
            "Geography": ["France", "Spain", "Germany"],
            "Gender": ["Male", "Female", "Female"],
            "Age": [30, 40, 35],
            "Tenure": [1, 5, 2],
            "Balance": [0.0, 10_000.0, 5000.0],
            "NumOfProducts": [1, 2, 2],
            "HasCrCard": [1, 0, 1],
            "IsActiveMember": [1, 0, 1],
            "EstimatedSalary": [50_000.0, 60_000.0, 70_000.0],
        }
    )
    y = np.array([0, 1, 0])
    cat_cols = ["Geography", "Gender"]
    num_cols = [c for c in raw.columns if c not in cat_cols]
    pre = ColumnTransformer(
        [
            ("num", StandardScaler(), num_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
        ]
    )
    pre.fit(raw)
    X_eng = engineered_feature_frame(pre, raw)
    clf = GradientBoostingClassifier(random_state=0)
    clf.fit(X_eng, y)
    return pre, clf


def test_churn_predictor_predict_matches_sklearn_directly():
    pre, clf = _toy_preprocessor_and_classifier()
    predictor = ChurnPredictor(
        preprocessor=pre,
        classifier=clf,
        run_id="local-test",
        model_version="0",
        registered_model_name="Local",
    )
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
    raw_df = request_to_single_row_df(payload)
    X = engineered_feature_frame(pre, raw_df)
    expected_p = float(clf.predict_proba(X)[0][list(clf.classes_).index(1)])

    out = predictor.predict(payload)
    assert out.prediction in (0, 1)
    assert abs(out.probability_churn - expected_p) < 1e-9
    assert out.mlflow_run_id == "local-test"
    assert out.model_version == "0"


def test_churn_predictor_from_pickle_roundtrip(tmp_path):
    """Save preprocessor and classifier as pickle files, then load via from_pickle."""
    pre, clf = _toy_preprocessor_and_classifier()

    preprocessor_path = tmp_path / "preprocessor.pkl"
    model_path = tmp_path / "model.pkl"

    with open(preprocessor_path, "wb") as f:
        pickle.dump(pre, f)
    with open(model_path, "wb") as f:
        pickle.dump(clf, f)

    predictor = ChurnPredictor.from_pickle(
        preprocessor_path=preprocessor_path,
        model_path=model_path,
    )

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
    out = predictor.predict(payload)

    # Results must match direct sklearn inference
    direct = ChurnPredictor(
        preprocessor=pre,
        classifier=clf,
        run_id="x",
        model_version="y",
        registered_model_name="z",
    ).predict(payload)

    assert out.prediction == direct.prediction
    assert out.probability_churn == direct.probability_churn


def test_churn_predictor_from_pickle_missing_file_raises(tmp_path):
    """from_pickle should raise FileNotFoundError for non-existent paths."""
    import pytest

    with pytest.raises(FileNotFoundError, match="Preprocessor pickle not found"):
        ChurnPredictor.from_pickle(
            preprocessor_path=tmp_path / "missing_preprocessor.pkl",
            model_path=tmp_path / "model.pkl",
        )