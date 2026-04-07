import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field


API_KEY_HEADER = "X-API-Key"
API_KEY_ENV_VAR = "API_KEY"

app = FastAPI(
    title="FocusTation ML Server",
    description="Simple scoring API for Android app integration.",
    version="0.1.0",
)


class ScoreRequest(BaseModel):
    feature1: float = Field(..., description="First feature value")
    feature2: float = Field(..., description="Second feature value")
    feature3: float = Field(..., description="Third feature value")


class ScoreResponse(BaseModel):
    score: float


def verify_api_key(x_api_key: str | None = Header(default=None, alias=API_KEY_HEADER)) -> None:
    expected_api_key = os.getenv(API_KEY_ENV_VAR)
    if not expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key is not configured on the server.",
        )

    if not x_api_key or not secrets.compare_digest(x_api_key, expected_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/score", response_model=ScoreResponse)
def calculate_score(
    payload: ScoreRequest,
    _: None = Depends(verify_api_key),
) -> ScoreResponse:
    score = payload.feature1 + payload.feature2 + payload.feature3
    return ScoreResponse(score=score)
