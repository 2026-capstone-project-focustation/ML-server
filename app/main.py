import os
import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

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
    description="ML scoring API for Android app integration.",
    version="0.2.0",
    lifespan=lifespan,
)


class ScoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_type: str = Field(..., description="User preference profile label")
    pref_quiet: float
    pref_light: float
    pref_low_crowd: float
    pref_privacy: float
    pref_outlet: float
    pref_distance: float
    pref_thermal_air: float
    pref_control: float
    pref_comfort: float
    pref_deepwork: float
    general_place_type: str
    general_task_type: str
    general_social_mode: str
    general_stay_duration: str
    general_time_slot: str
    general_distraction_noise: float
    general_distraction_crowd: float
    general_distraction_visual: float
    general_distraction_temperature: float
    general_distraction_outlet: float
    general_distraction_distance: float
    general_priority_quiet: float
    general_priority_outlet: float
    general_priority_distance: float
    general_priority_comfort: float
    general_priority_privacy: float
    place_type: str
    task_type: str
    group_size: str
    stay_duration: str
    time_slot: str
    day_type: str
    distance_minutes: float
    weather: str
    indoor_outdoor: str
    visit_frequency: str
    place_quiet: float
    place_light: float
    place_low_crowd: float
    place_low_visual_distraction: float
    place_control: float
    place_comfort: float
    place_outlet: float
    place_task_fit: float
    place_temperature_air: float
    place_seat_availability: float
    quiet_match: float
    light_match: float
    crowd_match: float
    privacy_match: float
    outlet_match: float
    thermal_air_match: float
    control_match: float
    comfort_match: float
    deepwork_task_match: float
    distance_penalty: float
    task_place_fit_match: float
    time_match: float


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
    payload: ScoreRequest,
    _: None = Depends(verify_api_key),
) -> ScoreResponse:
    try:
        score = predict_satisfaction(payload.model_dump())
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
