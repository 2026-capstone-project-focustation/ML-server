import os
import secrets
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel

from app.model_inference import load_model_bundle, predict_satisfaction


API_KEY_HEADER = "X-API-Key"
API_KEY_ENV_VAR = "API_KEY"


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Fail fast during startup if the model bundle is missing or invalid.
    load_model_bundle()
    yield


app = FastAPI(
    title="FocusTation ML Server",
    description="Sensor-aware ML scoring API for Android app integration.",
    version="0.3.0",
    lifespan=lifespan,
)


class ScoreResponse(BaseModel):
    score: float


def verify_api_key(x_api_key: str | None = Header(default=None, alias=API_KEY_HEADER)) -> None:
    expected_api_key = os.getenv(API_KEY_ENV_VAR)
    expected_api_key = expected_api_key.strip() if expected_api_key else None
    received_api_key = x_api_key.strip() if x_api_key else None
    if not expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key is not configured on the server.",
        )

    if not received_api_key or not secrets.compare_digest(received_api_key, expected_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/score", response_model=ScoreResponse)
def calculate_score(
    payload: dict[str, Any],
    _: None = Depends(verify_api_key),
) -> ScoreResponse:
    try:
        score = predict_satisfaction(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model file is not available on the server.",
        ) from exc

    return ScoreResponse(score=score)
