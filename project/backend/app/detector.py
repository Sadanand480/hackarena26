"""Person detector using OpenCV HOG (no PyTorch/ultralytics required).

If you later want YOLOv8, install ultralytics separately and set
USE_YOLO=1 in your environment — the detector will switch automatically.
"""
from __future__ import annotations
import os
import cv2
import numpy as np


class PersonDetector:
    def __init__(self, confidence: float = 0.4):
        self.confidence = confidence
        self._yolo = None

        if os.getenv("USE_YOLO", "0") == "1":
            try:
                from ultralytics import YOLO  # type: ignore
                model_path = os.getenv("YOLO_MODEL", "yolov8n.pt")
                self._yolo = YOLO(model_path)
                print("[Detector] YOLOv8 loaded.")
            except Exception as e:
                print(f"[Detector] YOLOv8 unavailable ({e}), falling back to HOG.")

        if self._yolo is None:
            self._hog = cv2.HOGDescriptor()
            self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            print("[Detector] Using OpenCV HOG person detector.")

    def detect(self, frame: np.ndarray) -> list[list[float]]:
        if self._yolo is not None:
            return self._yolo_detect(frame)
        return self._hog_detect(frame)

    # ── YOLO ──────────────────────────────────────────────────────────────────
    def _yolo_detect(self, frame: np.ndarray) -> list[list[float]]:
        results = self._yolo(frame, classes=[0], conf=self.confidence, verbose=False)
        boxes = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                boxes.append([x1, y1, x2, y2])
        return boxes

    # ── HOG ───────────────────────────────────────────────────────────────────
    def _hog_detect(self, frame: np.ndarray) -> list[list[float]]:
        # Resize for speed; HOG works best ~480p
        h, w = frame.shape[:2]
        scale = min(1.0, 640 / max(w, h))
        small = cv2.resize(frame, (int(w * scale), int(h * scale)))

        rects, weights = self._hog.detectMultiScale(
            small,
            winStride=(8, 8),
            padding=(4, 4),
            scale=1.05,
        )

        boxes = []
        if len(rects):
            for (x, y, bw, bh), weight in zip(rects, weights):
                if weight < 0.3:
                    continue
                # Scale back to original frame size
                x1 = x / scale
                y1 = y / scale
                x2 = (x + bw) / scale
                y2 = (y + bh) / scale
                boxes.append([float(x1), float(y1), float(x2), float(y2)])
        return boxes
