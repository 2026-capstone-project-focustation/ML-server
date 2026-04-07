from fastapi import FastAPI
from pydantic import BaseModel, Field


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


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/score", response_model=ScoreResponse)
def calculate_score(payload: ScoreRequest) -> ScoreResponse:
    score = payload.feature1 + payload.feature2 + payload.feature3
    return ScoreResponse(score=score)
