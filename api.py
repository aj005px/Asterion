from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Any
from datetime import datetime, timezone
from urllib.parse import urlparse
from storage.database import (
    connect_to_mongodb,
    save_tab_event,
    save_tab_duration,
    save_feedback,
)
from intelligence.compare_scores import compare_scores
from intelligence.features import get_domain_features
from intelligence.hybrid_ranking import compute_hybrid_scores
from intelligence.inference import inference

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


class TabCandidate(BaseModel):
    tab_id: Optional[int] = None
    url: str = Field(..., min_length=1)
    active: bool = False
    pinned: bool = False
    audible: bool = False
    discarded: bool = False
    window_id: Optional[int] = None


class TabsReviewRequest(BaseModel):
    tabs: List[TabCandidate] = Field(default_factory=list)


@app.on_event("startup")
def startup():
    try:
        connect_to_mongodb()
    except Exception as e:
        print(f"Warning: MongoDB not available at startup: {e}")


@app.get("/")
def root():
    return {"status": "ok", "service": "asterion-api", "scoring_version": SCORING_VERSION, "model_status": inference.status()}


@app.get("/model/status")
def model_status():
    try:
        return inference.status()
    except Exception as error:
        raise HTTPException(status_code=500, detail="Failed to get model status")



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
        # Use hybrid ML ranking (baseline + trained model) with safe fallback
        try:
            results = compute_hybrid_scores()
            if results:
                # compute_hybrid_scores already sorts by hybrid_score desc
                enriched = []
                for item in results:
                    enriched.append({
                        **item,
                        "scoring_version": SCORING_VERSION,
                    })
                # Determine overall ranking method
                if any(r.get("ml_used") for r in enriched):
                    ranking_method = "hybrid_ml_baseline"
                else:
                    ranking_method = "weighted_baseline"
                return {
                    "ranking_method": ranking_method,
                    "scoring_version": SCORING_VERSION,
                    "count": len(enriched),
                    "recommendations": enriched,
                    "model_status": inference.status(),
                }
        except Exception:
            # Fall through to baseline
            pass

        # Baseline fallback (preserved behavior)
        results = compare_scores()

        results.sort(
            key=lambda item: item.get("hybrid_score", item.get("weighted_score", 0)),
            reverse=True,
        )

        enriched = []
        for item in results:
            enriched.append({
                **item,
                "scoring_version": SCORING_VERSION,
                "ranking_method": "weighted_baseline",
                "ml_used": False,
            })

        return {
            "ranking_method": "weighted_baseline",
            "scoring_version": SCORING_VERSION,
            "count": len(enriched),
            "recommendations": enriched,
            "model_status": inference.status(),
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


def _is_excluded_url(url: str) -> bool:
    if not url:
        return True
    u = url.lower()
    if u.startswith("chrome://") or u.startswith("chrome-extension://"):
        return True
    if u.startswith("edge://") or u.startswith("about:"):
        return True
    if u.startswith("devtools://") or u.startswith("chrome-search://"):
        return True
    if u.startswith("chrome-untrusted://") or u.startswith("moz-extension://"):
        return True
    # Only consider normal http/https for review suggestions in general
    if not (u.startswith("http://") or u.startswith("https://")):
        return True
    return False


@app.post("/tabs/review")
def get_tabs_to_review(req: TabsReviewRequest):
    try:
        # Get domain features (real activity data)
        domain_features = get_domain_features()
        feat_by_domain = {f["domain"]: f for f in domain_features}

        # Also get recommendations structure for consistency if desired
        results = compare_scores()
        rec_by_domain = {r["domain"]: r for r in results}

        candidates_out = []
        for tab in req.tabs:
            url = tab.url or ""
            # Apply exclusions
            if tab.active:
                continue
            if tab.pinned:
                continue
            if tab.audible:
                continue
            if tab.discarded:
                continue
            if _is_excluded_url(url):
                continue

            try:
                parsed = urlparse(url)
                domain = parsed.hostname
            except Exception:
                domain = None

            if not domain:
                continue

            feat = feat_by_domain.get(domain)
            rec = rec_by_domain.get(domain)

            reasons = []
            evidence = {}
            if feat is not None:
                evidence = {
                    "total_time_seconds": feat.get("total_time_seconds"),
                    "activation_count": feat.get("activation_count"),
                    "recency_seconds": feat.get("recency_seconds"),
                }
                # Build evidence-based reasons
                if feat.get("total_time_seconds") is not None and feat.get("total_time_seconds") < 60:
                    reasons.append("Low total time spent")
                elif feat.get("total_time_seconds") is not None and feat.get("total_time_seconds") < 300:
                    reasons.append("Short recorded time")
                if feat.get("activation_count") is not None and feat.get("activation_count") <= 1:
                    reasons.append("Few activations")
                if feat.get("recency_seconds") is not None and feat.get("recency_seconds") > 3600:
                    reasons.append("Not used recently")
                if rec is not None and rec.get("weighted_score") is not None and rec.get("weighted_score") < 0.2:
                    reasons.append("Low ranking score")
            else:
                reasons = ["Not enough activity data"]

            # Ranking: prefer low weighted score / low recency/low time? Suggest closing tabs that are likely less useful
            # Use inverse of weighted score as "review" priority (lower is more candidate)
            review_score = 0.0
            if rec is not None and rec.get("weighted_score") is not None:
                review_score = max(0.0, 1.0 - float(rec.get("weighted_score")))
            elif feat is not None:
                # Fallback using raw signals
                t = feat.get("total_time_seconds") or 0.0
                a = feat.get("activation_count") or 0
                r = feat.get("recency_seconds") or 10**9
                # lower is better for review
                review_score = 1.0 / (1.0 + t / 60.0 + a + 1.0 / (1.0 + r / 3600.0))
            else:
                review_score = 0.5  # unknown, still candidate if no strong evidence - but mark reason

            candidates_out.append(
                {
                    "tab_id": tab.tab_id,
                    "url": url,
                    "domain": domain,
                    "active": tab.active,
                    "pinned": tab.pinned,
                    "audible": tab.audible,
                    "reasons": reasons,
                    "evidence": evidence,
                    "review_score": round(float(review_score), 4),
                    "ranking_method": "inverse_weighted_baseline" if rec is not None else "signal_fallback",
                    "scoring_version": SCORING_VERSION,
                }
            )

        # Sort by review_score desc (higher priority to review)
        candidates_out.sort(key=lambda x: x.get("review_score", 0), reverse=True)

        return {
            "count": len(candidates_out),
            "tabs_to_review": candidates_out,
            "ranking_method": "inverse_weighted_baseline",
            "scoring_version": SCORING_VERSION,
        }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute tabs to review",
        )
