# ZeroDay — CCTV Threat Detection

Full-stack threat detection system using trained scene-specific ML classifiers.

## Stack
- **Backend**: FastAPI + OpenCV + YOLOv8 + scikit-learn
- **Frontend**: React (Vite) — dark ops-centre dashboard
- **DB**: MongoDB
- **Infra**: Docker Compose

## Models
Three trained classifiers live in `models/`:
| File | Purpose |
|---|---|
| `railway_clf.joblib` | Threat scoring in railway scenes |
| `industrial_clf.joblib` | Threat scoring in industrial scenes |
| `aggression_clf.joblib` | General aggression detection |

Each classifier is paired with a `*_scaler.joblib` and expects **18 features**
extracted from bounding-box tracking (speed, direction, crowd density, zone risk, etc.).

## Quick Start (Docker)
```bash
docker compose up --build
```
- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

## Quick Start (Manual)
```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
MODELS_DIR=../models uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install && npm run dev
```

## Environment Variables
See `.env.example` — copy to `.env` and adjust.

| Variable | Default | Description |
|---|---|---|
| `ALERT_THRESHOLD` | 60 | Min score to log an event |
| `FRAME_SKIP` | 5 | Analyse every Nth frame |
| `MAX_FRAMES` | 300 | Frame cap per upload |
| `MODELS_DIR` | `models` | Path to joblib files |

## Pipeline
1. Video upload → OpenCV frame extraction
2. YOLOv8 person detection (auto-downloads `yolov8n.pt`)
3. CentroidTracker assigns persistent IDs
4. FeatureExtractor computes 18 features per track
5. Scene-specific classifier predicts threat score
6. Events ≥ threshold stored in MongoDB
7. Dashboard polls & displays results live
