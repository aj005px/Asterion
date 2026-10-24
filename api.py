from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal, Optional
from storage.database import (
    connect_to_mongodb,
    save_tab_event,
    save_tab_duration,
    save_feedback,
)
from intelligence.compare_scores import compare_scores

SCORING_VERSION = "v2"

app = FastAPI(title="Asterion API", description="Local-first tab prioritization API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TabEvent(BaseModel):
    url: str = Field(..., min_length=1)
    tab_id: Optional[int] = None
    session_id: Optional[str] = None


class TabDuration(BaseModel):
    url: str = Field(..., min_length=1)
    tab_id: Optional[int] = None
    session_id: Optional[str] = None
    duration_seconds: float = Field(..., ge=0)


class FeedbackEvent(BaseModel):
    domain: str = Field(..., min_length=1)
    label: Literal["useful", "not_useful"]
    weighted_score: float = Field(..., ge=0, le=1)
    time_score: float = Field(..., ge=0, le=1)
    activation_score: float = Field(..., ge=0, le=1)
    recency_score: float = Field(..., ge=0, le=1)
    is_test: bool = False
    feature_snapshot: Optional[dict] = None


@app.on_event("startup")
def startup():
    try:
        connect_to_mongodb()
    except Exception as e:
        print(f"Warning: MongoDB not available at startup: {e}")


@app.get("/")
def root():
    return {"status": "ok", "service": "asterion-api", "scoring_version": SCORING_VERSION}


@app.post("/tab/activate")
def activate(event: TabEvent):
    try:
        event_id = save_tab_event(
            event.url,
            event.tab_id,
            event.session_id,
        )
        return {
            "message": "Tab event saved",
            "received_url": event.url,
            "event_id": event_id,
        }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save tab event",
        )


@app.post("/tab/duration")
def record_duration(event: TabDuration):
    try:
        if event.duration_seconds <= 0:
            raise HTTPException(status_code=400, detail="duration_seconds must be greater than 0")
        event_id = save_tab_duration(
            event.url,
            event.tab_id,
            event.session_id,
            event.duration_seconds,
        )
        return {
            "message": "Tab duration saved",
            "duration_seconds": event.duration_seconds,
            "event_id": event_id,
        }
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save tab duration",
        )


@app.get("/recommendations")
def get_recommendations():
    try:
        results = compare_scores()

        results.sort(
            key=lambda item: item.get("weighted_score", 0),
            reverse=True,
        )

        enriched = []
        for item in results:
            enriched.append({
                **item,
                "scoring_version": SCORING_VERSION,
                "ranking_method": "weighted_baseline",
            })

        return {
            "ranking_method": "weighted_baseline",
            "scoring_version": SCORING_VERSION,
            "count": len(enriched),
            "recommendations": enriched,
        }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate recommendations",
        )


@app.post("/feedback")
def record_feedback(event: FeedbackEvent):
    try:
        event_id = save_feedback(
            event.domain,
            event.label,
            event.weighted_score,
            event.time_score,
            event.activation_score,
            event.recency_score,
            SCORING_VERSION,
            event.is_test,
            event.feature_snapshot,
        )

        return {
            "message": "Feedback saved",
            "event_id": event_id,
            "scoring_version": SCORING_VERSION,
        }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save feedback",
        )
