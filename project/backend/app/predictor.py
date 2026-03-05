"""Load trained sklearn classifiers and run inference.

Falls back to heuristic scoring if models fail to load (e.g. sklearn version mismatch).
"""
from __future__ import annotations

import os
import warnings
from pathlib import Path

import numpy as np

MODELS_DIR = Path(os.getenv("MODELS_DIR", "models"))

THREAT_LABELS = {
    (0, 40): "Normal",
    (40, 60): "Moderate Risk",
    (60, 80): "Suspicious Behaviour",
    (80, 101): "High Threat",
}


def _label(score: int) -> str:
    for (lo, hi), label in THREAT_LABELS.items():
        if lo <= score < hi:
            return label
    return "High Threat"


class ThreatPredictor:
    def __init__(self):
        self.models: dict = {}
        self.scalers: dict = {}
        self._load_models()

    def _load_models(self):
        try:
            import joblib
        except ImportError:
            print("[Predictor] joblib not installed. Using heuristic scoring.")
            return

        for scene in ("railway", "industrial", "aggression"):
            clf_p = MODELS_DIR / f"{scene}_clf.joblib"
            scl_p = MODELS_DIR / f"{scene}_scaler.joblib"
            if not clf_p.exists() or not scl_p.exists():
                print(f"[Predictor] Model files missing for '{scene}', skipping.")
                continue
            try:
                self.models[scene] = joblib.load(clf_p)
                self.scalers[scene] = joblib.load(scl_p)
                print(f"[Predictor] Loaded '{scene}' model.")
            except Exception as exc:
                warnings.warn(
                    f"[Predictor] Could not load '{scene}' model: {exc}. "
                    "Will use heuristic scoring for this scene."
                )

        if not self.models:
            print("[Predictor] No models loaded — falling back to heuristic scoring.")

    def predict(self, features: np.ndarray, scene: str) -> tuple[int, str]:
        """Return (threat_score 0-100, threat_type)."""
        key = scene if scene in self.models else next(iter(self.models), None)

        if key is None:
            return self._heuristic(features)

        try:
            X = features.reshape(1, -1)
            X_scaled = self.scalers[key].transform(X)
            proba = self.models[key].predict_proba(X_scaled)[0]
            threat_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
            score = int(round(threat_prob * 100))
        except Exception as exc:
            warnings.warn(f"[Predictor] Inference failed ({exc}), using heuristic.")
            return self._heuristic(features)

        score = max(0, min(100, score))
        return score, _label(score)

    @staticmethod
    def _heuristic(features: np.ndarray) -> tuple[int, str]:
        """Fallback scoring from raw features when no model is available."""
        # features: speed_norm[0], direction_change[2], closing_speed[9],
        #           surround_count[8], dwell[11]
        weights = np.zeros(len(features))
        idx_map = {0: 0.25, 2: 0.2, 9: 0.25, 8: 0.15, 11: 0.15}
        for i, w in idx_map.items():
            if i < len(weights):
                weights[i] = w
        score = int(np.dot(features, weights) * 100)
        score = max(0, min(100, score))
        return score, _label(score)
