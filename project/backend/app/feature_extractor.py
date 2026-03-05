"""Extract the 18 features expected by the trained classifiers."""
import numpy as np
from .tracker import Track


class FeatureExtractor:
    def __init__(self, fps: float = 25.0, frame_w: int = 640, frame_h: int = 480):
        self.fps = fps
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.diag = float(np.sqrt(frame_w ** 2 + frame_h ** 2))

    def extract(self, track: Track, scene: str, all_tracks: dict) -> np.ndarray:
        """Return float32 array of shape (18,) matching metadata.json feature order."""
        history = track.history
        n = len(history)
        centroids = [((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) for b in history]
        D = self.diag

        # ── speed features ────────────────────────────────────────────────────
        if n >= 2:
            speeds = [
                np.sqrt(
                    (centroids[i][0] - centroids[i - 1][0]) ** 2
                    + (centroids[i][1] - centroids[i - 1][1]) ** 2
                ) / D
                for i in range(1, n)
            ]
            speed_norm = float(np.mean(speeds))
            speed_variance_norm = float(np.var(speeds))
            speed_trend = float(speeds[-1] - speeds[0]) if len(speeds) > 1 else 0.0
        else:
            speed_norm = speed_variance_norm = speed_trend = 0.0

        # ── direction changes ─────────────────────────────────────────────────
        if n >= 3:
            angles = []
            for i in range(1, n - 1):
                v1 = (centroids[i][0] - centroids[i - 1][0], centroids[i][1] - centroids[i - 1][1])
                v2 = (centroids[i + 1][0] - centroids[i][0], centroids[i + 1][1] - centroids[i][1])
                mag1 = np.sqrt(v1[0] ** 2 + v1[1] ** 2) + 1e-6
                mag2 = np.sqrt(v2[0] ** 2 + v2[1] ** 2) + 1e-6
                cos_a = np.clip((v1[0] * v2[0] + v1[1] * v2[1]) / (mag1 * mag2), -1, 1)
                angles.append(float(np.arccos(cos_a) / np.pi))
            direction_change_norm = float(np.mean(angles))
        else:
            direction_change_norm = 0.0

        # ── scene flags ───────────────────────────────────────────────────────
        in_railway = 1.0 if scene == "railway" else 0.0
        in_industrial = 1.0 if scene == "industrial" else 0.0

        # ── positional / zone risk ────────────────────────────────────────────
        last_bbox = history[-1]
        cx_n = (last_bbox[0] + last_bbox[2]) / (2 * self.frame_w)  # 0-1
        cy_n = (last_bbox[1] + last_bbox[3]) / (2 * self.frame_h)  # 0-1
        zone_risk_norm = float(cy_n * 0.5 + abs(cx_n - 0.5) * 0.5)

        # ── other-person stats ────────────────────────────────────────────────
        other_centroids = []
        for tid, t in all_tracks.items():
            if tid != track.id and t.history:
                ob = t.history[-1]
                other_centroids.append(((ob[0] + ob[2]) / 2, (ob[1] + ob[3]) / 2))

        cx_curr, cy_curr = centroids[-1]
        scene_density_norm = min(len(other_centroids) / 20.0, 1.0)
        in_crowd = 1.0 if len(other_centroids) >= 5 else 0.0

        if other_centroids:
            dists = [
                np.sqrt((ox - cx_curr) ** 2 + (oy - cy_curr) ** 2) / D
                for ox, oy in other_centroids
            ]
            nearest_dist_norm = float(min(dists))
            surround_count = sum(1 for d in dists if d < 0.15)
            surround_count_norm = min(surround_count / 10.0, 1.0)

            if n >= 5:
                cx_p, cy_p = centroids[-5]
                dists_prev = [
                    np.sqrt((ox - cx_p) ** 2 + (oy - cy_p) ** 2) / D
                    for ox, oy in other_centroids
                ]
                closing_speed_norm = float(max(0.0, min(dists_prev) - nearest_dist_norm))
            else:
                closing_speed_norm = 0.0

            cluster_size = sum(
                1 for ox, oy in other_centroids
                if np.sqrt((ox - cx_curr) ** 2 + (oy - cy_curr) ** 2) / D < 0.2
            )
            cluster_size_norm = min(cluster_size / 10.0, 1.0)
        else:
            nearest_dist_norm = 1.0
            surround_count_norm = 0.0
            closing_speed_norm = 0.0
            cluster_size_norm = 0.0

        # ── dwell ─────────────────────────────────────────────────────────────
        if n >= 2:
            total_disp = (
                np.sqrt(
                    (centroids[-1][0] - centroids[0][0]) ** 2
                    + (centroids[-1][1] - centroids[0][1]) ** 2
                )
                / D
            )
            dwell_norm = float(max(0.0, 1.0 - total_disp * 5))
        else:
            dwell_norm = 0.0

        # ── runner ratio ──────────────────────────────────────────────────────
        if all_tracks:
            runner_count = 0
            for t in all_tracks.values():
                if len(t.history) >= 2:
                    tc = [((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) for b in t.history]
                    sp = np.sqrt((tc[-1][0] - tc[-2][0]) ** 2 + (tc[-1][1] - tc[-2][1]) ** 2) / D
                    if sp > 0.02:
                        runner_count += 1
            runner_ratio = runner_count / max(len(all_tracks), 1)
        else:
            runner_ratio = 0.0

        # ── pose (stub — requires pose model) ────────────────────────────────
        arm_speed_norm = 0.0
        wrist_height_norm = 0.0
        torso_lean_norm = 0.0

        features = np.array(
            [
                speed_norm, speed_variance_norm, direction_change_norm,
                in_railway, in_industrial, in_crowd,
                zone_risk_norm, nearest_dist_norm, surround_count_norm,
                closing_speed_norm, cluster_size_norm, dwell_norm,
                speed_trend, runner_ratio, scene_density_norm,
                arm_speed_norm, wrist_height_norm, torso_lean_norm,
            ],
            dtype=np.float32,
        )
        return np.clip(features, 0.0, 1.0)
