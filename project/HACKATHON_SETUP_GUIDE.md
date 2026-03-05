# CCTV Threat Detection Hackathon Setup Guide

This guide turns your project idea into a practical setup you can run quickly.

## 1) Main Development Environment

Use **Visual Studio Code** as your primary IDE.

Why VS Code:
- Great support for **Python + React + Docker**
- Built-in terminal for fast iteration
- Easy debugger integration
- Strong extension ecosystem for AI projects

Recommended VS Code extensions:
- Python
- Pylance
- Docker
- Jupyter
- GitHub Copilot (optional)

## 2) Backend Language and Libraries

Build the backend in **Python**.

Core stack:
- **FastAPI** for the API server
- **OpenCV** for frame/video processing
- **YOLOv8** for person detection
- **ByteTrack** for multi-object tracking
- **scikit-learn** for lightweight threat scoring models

## 3) Frontend Dashboard

Build the dashboard with **React**.

Dashboard should display:
- Video playback
- Bounding boxes and tracked IDs
- Threat score
- Alert feed
- Clip/event history

Frontend communicates with backend through REST APIs.

## 4) Data Storage

Use **MongoDB** to store alerts, events, and clip metadata.

Example event document:

```json
{
  "person_id": 3,
  "threat_score": 92,
  "type": "Aggressive Behaviour",
  "timestamp": "2026-03-05T21:30"
}
```

## 5) Containerization

Use **Docker Compose** to run backend, frontend, and MongoDB together.

Run everything with:

```bash
docker-compose up --build
```

## 6) Hardware Requirements (Hackathon-Friendly)

Minimum recommended:
- 16 GB RAM
- 20 GB free storage
- Intel i5 / Ryzen 5 or better

GPU is optional for the demo phase:
- YOLOv8 can run on CPU (slower but acceptable for prerecorded videos)
- Threat model can remain lightweight (e.g., GradientBoosting)

## 7) Demo Video Folder Structure

Create a local folder:

```text
videos/
  railway.mp4
  industry.mp4
  aggression.mp4
```

Use prerecorded CCTV-style videos for predictable demos.

## 8) Local Run Flow (Without Docker)

1. Open project folder in VS Code
2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Start backend:

```bash
uvicorn backend.main:app --reload
```

4. Start frontend:

```bash
npm start
```

5. Upload/select a video and view detections in the dashboard.

## 9) Recommended Project Organization

```text
project-root/
  backend/
  frontend/
  models/
  videos/
  docker-compose.yml
```

## 10) Fast 6-8 Hour Hackathon Execution Plan

### Hour 1
- Scaffold FastAPI + React + MongoDB services
- Wire Docker Compose

### Hour 2
- Add video upload/select endpoint
- Add frame extraction pipeline

### Hour 3
- Integrate YOLOv8 detection
- Return bounding boxes with timestamps

### Hour 4
- Add ByteTrack IDs per person
- Persist detections to MongoDB

### Hour 5
- Add heuristic/ML threat scoring
- Trigger alert events above threshold

### Hour 6
- Build dashboard panels (video + alerts + score)
- Hook APIs end-to-end

### Hour 7
- Polish UI and add sample clips
- Add per-environment demo toggles

### Hour 8
- Dry run presentation + record fallback video
- Prepare concise architecture slide

## Quick Demo Advice

For a hackathon, focus on **three scenes** only:
1. Railway station
2. Industrial area
3. Aggressive/fight clip

This is enough to show multi-environment behavior detection with clear value.
