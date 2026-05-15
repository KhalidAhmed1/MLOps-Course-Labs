import os

import pytest

from churn_api.telemetry import (
    hyperdx_enabled,
    init_hyperdx_from_env,
    instrument_fastapi_app,
    instrument_logging_for_hyperdx,
    reset_hyperdx_state,
)


def test_hyperdx_enabled_false_without_api_key():
    assert hyperdx_enabled() is False


def test_hyperdx_enabled_respects_disable_flag(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HYPERDX_API_KEY", "test-key")
    monkeypatch.setenv("CHURN_API_DISABLE_HYPERDX", "1")
    assert hyperdx_enabled() is False


def test_init_hyperdx_no_op_without_key():
    reset_hyperdx_state()
    assert init_hyperdx_from_env() is False


def test_instrument_helpers_no_op_without_sdk(monkeypatch: pytest.MonkeyPatch):
    """Logging/FastAPI shims should not raise when HyperDX is off."""
    monkeypatch.delenv("HYPERDX_API_KEY", raising=False)
    reset_hyperdx_state()
    instrument_logging_for_hyperdx()
    instrument_fastapi_app(object())
