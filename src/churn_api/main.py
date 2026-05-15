"""FastAPI application: routes, logging, and model lifecycle."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from churn_api.schemas import ChurnPredictRequest, ChurnPredictResponse
from churn_api.service import ChurnPredictor
from churn_api import telemetry

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Console logging for local runs + optional HyperDX (OTEL) export."""
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    telemetry.init_hyperdx_from_env()
    telemetry.instrument_logging_for_hyperdx()

    for name in ("churn_api", "churn_api.main", "churn_api.service", "churn_api.features"):
        logging.getLogger(name).setLevel(logging.INFO)


def get_predictor(request: Request) -> ChurnPredictor:
    predictor = getattr(request.app.state, "predictor", None)
    if predictor is None:
        logger.error("predictor missing on app.state")
        raise HTTPException(status_code=503, detail="Model not loaded")
    return predictor


PredictorDep = Annotated[ChurnPredictor, Depends(get_predictor)]


def create_app(*, predictor: ChurnPredictor | None = None) -> FastAPI:
    """
    Build the FastAPI app.

    ``predictor`` is injected for tests; when omitted, the lifespan loads
    from the hardcoded pickle paths in service.py.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("lifespan.start service=churn_api")
        if predictor is not None:
            app.state.predictor = predictor
            logger.info("lifespan using injected predictor")
        else:
            try:
                app.state.predictor = ChurnPredictor.from_pickle()
            except Exception:
                logger.exception("lifespan failed to load model")
                raise
        logger.info("lifespan.ready")
        yield
        logger.info("lifespan.shutdown")

    app = FastAPI(
        title="Bank churn prediction API",
        description="Serves a pickle-based champion model for the MLOps course lab.",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next: Any):
        start = time.perf_counter()
        logger.info(
            "http.request.start method=%s path=%s client=%s",
            request.method,
            request.url.path,
            request.client.host if request.client else None,
        )
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "http.request.error method=%s path=%s",
                request.method,
                request.url.path,
            )
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "http.request.end method=%s path=%s status=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    @app.get("/", tags=["meta"])
    async def home() -> dict[str, str]:
        logger.info("route.home")
        return {
            "service": "Bank churn prediction API",
            "description": "Champion model loaded from local pickle files.",
            "docs": "/docs",
            "health": "/health",
            "predict": "/predict",
        }

    @app.get("/health", tags=["meta"])
    async def health(request: Request) -> JSONResponse:
        pred = getattr(request.app.state, "predictor", None)
        body: dict[str, Any] = {
            "status": "ok" if pred is not None else "degraded",
            "model_loaded": pred is not None,
        }
        if pred is not None:
            body["model_version"] = pred.model_version
        logger.info("route.health payload=%s", body)
        status_code = 200 if pred is not None else 503
        return JSONResponse(content=body, status_code=status_code)

    @app.post("/predict", response_model=ChurnPredictResponse, tags=["inference"])
    async def predict_endpoint(
        body: ChurnPredictRequest,
        svc: PredictorDep,
    ) -> ChurnPredictResponse:
        try:
            return svc.predict(body)
        except HTTPException:
            raise
        except Exception:
            logger.exception("predict.unhandled_error")
            raise HTTPException(status_code=500, detail="Prediction failed") from None

    telemetry.instrument_fastapi_app(app)
    return app


configure_logging()
app = create_app()