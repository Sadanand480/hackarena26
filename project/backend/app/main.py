from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from typing import Optional

import cv2
from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware

from .database import MongoRepo
from .schemas import ThreatEvent, ThreatResponse, AnalysisResult
from .detector import PersonDetector
from .tracker import CentroidTracker
from .feature_extractor import FeatureExtractor
from .predictor import ThreatPredictor

# ── app setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="CCTV Threat Detection API", version="1.0.0")
repo = MongoRepo()

# One shared instance of each heavy object
detector = PersonDetector()
predictor = ThreatPredictor()

origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
origins = [o.strip() for o in origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALERT_THRESHOLD = int(os.getenv("ALERT_THRESHOLD", "60"))
FRAME_SKIP = int(os.getenv("FRAME_SKIP", "5"))      # analyse every Nth frame
MAX_FRAMES = int(os.getenv("MAX_FRAMES", "300"))     # cap per upload


# ── helpers ───────────────────────────────────────────────────────────────────

def _process_video(path: str, scene: str, filename: str) -> AnalysisResult:
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480

    tracker = CentroidTracker(max_lost=10)
    extractor = FeatureExtractor(fps=fps, frame_w=w, frame_h=h)

    events: list[ThreatEvent] = []
    frame_idx = 0
    processed = 0

    while True:
        ret, frame = cap.read()
        if not ret or processed >= MAX_FRAMES:
            break
        frame_idx += 1
        if frame_idx % FRAME_SKIP != 0:
            continue
        processed += 1

        detections = detector.detect(frame)
        tracks = tracker.update(detections, frame_idx)

        for tid, track in tracks.items():
            if len(track.history) < 3:
                continue
            features = extractor.extract(track, scene, tracks)
            score, label = predictor.predict(features, scene)

            if score >= ALERT_THRESHOLD:
                event = ThreatEvent(
                    person_id=tid,
                    threat_score=score,
                    type=label,
                    timestamp=datetime.now(timezone.utc),
                    source_video=filename,
                    scene=scene,
                    bbox=track.bbox,
                    frame_idx=frame_idx,
                )
                events.append(event)
                repo.insert_event(event.model_dump(mode="json"))

    cap.release()

    persons = len({e.person_id for e in events})
    max_score = max((e.threat_score for e in events), default=0)
    return AnalysisResult(
        status="ok",
        message=f"Processed {processed} frames from '{filename}'",
        total_frames=processed,
        persons_detected=persons,
        alerts=len(events),
        events=events,
        max_threat_score=max_score,
        scene=scene,
    )


# ── routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    loaded = list(predictor.models.keys())
    return {"status": "ok", "models_loaded": loaded, "alert_threshold": ALERT_THRESHOLD}


@app.get("/api/events")
def get_events(limit: int = Query(50, ge=1, le=200)) -> dict:
    return {"items": repo.list_events(limit=limit)}


@app.delete("/api/events")
def clear_events() -> dict:
    repo.clear_events()
    return {"status": "ok", "message": "All events cleared"}


@app.post("/api/analyze", response_model=AnalysisResult)
async def analyze_video(
    file: UploadFile = File(...),
    scene: str = Query("aggression", regex="^(railway|industrial|aggression)$"),
) -> AnalysisResult:
    suffix = os.path.splitext(file.filename or "clip")[1] or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        result = _process_video(tmp_path, scene, file.filename or "upload")
    finally:
        os.unlink(tmp_path)

    return result
