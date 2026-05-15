"""
HyperDX integration (OpenTelemetry).

Live logs, traces, and metrics are shipped when ``HYPERDX_API_KEY`` is set.
See https://www.hyperdx.io/docs/install/python
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_hyperdx_sdk_configured = False
_fastapi_instrumented = False
_logging_instrumented = False


def hyperdx_enabled() -> bool:
    """True when HyperDX export should be turned on (API key present)."""
    if os.environ.get("CHURN_API_DISABLE_HYPERDX", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        return False
    return bool(os.environ.get("HYPERDX_API_KEY", "").strip())


def init_hyperdx_from_env() -> bool:
    """
    Configure the HyperDX OpenTelemetry distro (exporter + global providers).

    Safe to call multiple times; only the first successful call configures the SDK.
    Returns whether HyperDX export is active after this call.
    """
    global _hyperdx_sdk_configured

    if not hyperdx_enabled():
        logger.debug("HyperDX disabled (no HYPERDX_API_KEY or explicitly disabled).")
        return False

    if _hyperdx_sdk_configured:
        return True

    try:
        from hyperdx.opentelemetry import configure_opentelemetry
    except ImportError:
        logger.warning(
            "HYPERDX_API_KEY is set but hyperdx-opentelemetry is not installed; "
            "install dependencies from requirements.txt."
        )
        return False

    os.environ.setdefault("OTEL_SERVICE_NAME", "bank-churn-api")
    os.environ.setdefault(
        "OTEL_RESOURCE_ATTRIBUTES",
        "deployment.environment=dev",
    )

    try:
        configure_opentelemetry()
    except Exception:
        logger.exception("HyperDX configure_opentelemetry failed.")
        return False

    _hyperdx_sdk_configured = True
    logger.info(
        "HyperDX OpenTelemetry configured (service=%s).",
        os.environ.get("OTEL_SERVICE_NAME"),
    )
    return True


def instrument_logging_for_hyperdx() -> None:
    """Bridge stdlib ``logging`` records to OpenTelemetry (visible as live logs in HyperDX)."""
    global _logging_instrumented

    if not hyperdx_enabled() or not _hyperdx_sdk_configured:
        return
    if _logging_instrumented:
        return
    try:
        from opentelemetry.instrumentation.logging import LoggingInstrumentor
    except ImportError:
        logger.warning(
            "opentelemetry-instrumentation-logging is not installed; "
            "stdlib logs will not be exported to HyperDX."
        )
        return

    LoggingInstrumentor().instrument(set_logging_format=False)
    _logging_instrumented = True
    logger.info("HyperDX logging instrumentation enabled (stdlib -> OTEL).")


def instrument_fastapi_app(app: Any) -> None:
    """Add FastAPI/Starlette HTTP tracing (spans correlate with logs in HyperDX)."""
    global _fastapi_instrumented

    if not hyperdx_enabled() or not _hyperdx_sdk_configured:
        return
    if _fastapi_instrumented:
        return

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    except ImportError:
        logger.warning(
            "opentelemetry-instrumentation-fastapi is not installed; "
            "HTTP traces will not be exported to HyperDX."
        )
        return

    FastAPIInstrumentor.instrument_app(app)
    _fastapi_instrumented = True
    logger.info("HyperDX FastAPI auto-instrumentation enabled.")


def reset_hyperdx_state() -> None:
    """Reset process-wide flags (used by tests; not for production)."""
    global _hyperdx_sdk_configured, _fastapi_instrumented, _logging_instrumented
    _hyperdx_sdk_configured = False
    _fastapi_instrumented = False
    _logging_instrumented = False
