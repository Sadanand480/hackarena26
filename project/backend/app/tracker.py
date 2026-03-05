"""Simple IoU-based centroid tracker (ByteTrack-lite)."""
import numpy as np


class Track:
    def __init__(self, track_id: int, bbox: list, frame_idx: int):
        self.id = track_id
        self.bbox = bbox          # [x1, y1, x2, y2]
        self.history = [bbox]
        self.frame_history = [frame_idx]
        self.lost_frames = 0

    @property
    def centroid(self):
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def update(self, bbox: list, frame_idx: int):
        self.bbox = bbox
        self.history.append(bbox)
        self.frame_history.append(frame_idx)
        self.lost_frames = 0


def _iou(a, b) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    a_area = (ax2 - ax1) * (ay2 - ay1)
    b_area = (bx2 - bx1) * (by2 - by1)
    return inter / (a_area + b_area - inter + 1e-6)


class CentroidTracker:
    def __init__(self, max_lost: int = 10, iou_threshold: float = 0.3):
        self.tracks: dict[int, Track] = {}
        self.next_id = 0
        self.max_lost = max_lost
        self.iou_threshold = iou_threshold

    def update(self, detections: list, frame_idx: int) -> dict[int, Track]:
        """detections: list of [x1, y1, x2, y2]."""
        if not detections:
            for t in self.tracks.values():
                t.lost_frames += 1
            self._remove_lost()
            return dict(self.tracks)

        if not self.tracks:
            for det in detections:
                self.tracks[self.next_id] = Track(self.next_id, det, frame_idx)
                self.next_id += 1
            return dict(self.tracks)

        track_ids = list(self.tracks.keys())
        matched_tracks: set[int] = set()
        matched_dets: set[int] = set()

        for i, det in enumerate(detections):
            best_score, best_tid = self.iou_threshold, None
            for tid in track_ids:
                if tid in matched_tracks:
                    continue
                score = _iou(det, self.tracks[tid].bbox)
                if score > best_score:
                    best_score, best_tid = score, tid
            if best_tid is not None:
                self.tracks[best_tid].update(det, frame_idx)
                matched_tracks.add(best_tid)
                matched_dets.add(i)

        for i, det in enumerate(detections):
            if i not in matched_dets:
                self.tracks[self.next_id] = Track(self.next_id, det, frame_idx)
                self.next_id += 1

        for tid in track_ids:
            if tid not in matched_tracks:
                self.tracks[tid].lost_frames += 1

        self._remove_lost()
        return dict(self.tracks)

    def _remove_lost(self):
        self.tracks = {
            tid: t for tid, t in self.tracks.items()
            if t.lost_frames <= self.max_lost
        }
