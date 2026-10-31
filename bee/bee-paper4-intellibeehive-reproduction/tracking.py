#!/usr/bin/env python3
"""Paper-faithful midpoint tracker and trigger-line counter.

IntelliBeeHive associates detections with the nearest previous midpoint inside a
50-pixel tolerance at 640 px width. Profiles unmatched for one frame are removed.
The upper and lower thirds of the frame produce Arriving and Leaving events.
This module keeps those rules visible and configurable rather than hiding them
inside a third-party tracker.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot
from typing import Iterable


@dataclass
class Detection:
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float = 1.0
    source_id: int | None = None

    @property
    def midpoint(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    @property
    def longest_side(self) -> float:
        return max(self.x2 - self.x1, self.y2 - self.y1)


@dataclass
class Profile:
    track_id: int
    midpoint: tuple[float, float]
    status: str = "New"
    bee_size_px: float | None = None
    source_ids: list[int] = field(default_factory=list)


class IntelliBeeTracker:
    def __init__(self, frame_width: int, frame_height: int, tolerance: float | None = None):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.tolerance = tolerance if tolerance is not None else 50.0 * frame_width / 640.0
        self.upper = frame_height / 3.0
        self.lower = 2.0 * frame_height / 3.0
        self.active: dict[int, Profile] = {}
        self.next_id = 1
        self.counts = {"Arriving": 0, "Leaving": 0}
        self.events: list[dict] = []

    def _crossing_status(self, previous_y: float, current_y: float) -> str | None:
        if previous_y > self.upper >= current_y:
            return "Arriving"
        if previous_y <= self.upper < current_y:
            return "Deck"
        if previous_y < self.lower <= current_y:
            return "Leaving"
        if previous_y >= self.lower > current_y:
            return "Deck"
        return None

    def update(self, detections: Iterable[Detection], frame_index: int) -> list[Profile]:
        detections = list(detections)
        candidates = []
        for track_id, profile in self.active.items():
            px, py = profile.midpoint
            for detection_index, detection in enumerate(detections):
                dx, dy = detection.midpoint
                distance = hypot(dx - px, dy - py)
                if distance <= self.tolerance:
                    candidates.append((distance, track_id, detection_index))
        candidates.sort()
        assigned_tracks: set[int] = set()
        assigned_detections: set[int] = set()
        matches = []
        for _, track_id, detection_index in candidates:
            if track_id in assigned_tracks or detection_index in assigned_detections:
                continue
            assigned_tracks.add(track_id)
            assigned_detections.add(detection_index)
            matches.append((track_id, detection_index))

        next_active: dict[int, Profile] = {}
        for track_id, detection_index in matches:
            previous = self.active[track_id]
            detection = detections[detection_index]
            current = detection.midpoint
            status = self._crossing_status(previous.midpoint[1], current[1]) or previous.status
            bee_size = previous.bee_size_px
            if status in {"Arriving", "Leaving"} and status != previous.status:
                self.counts[status] += 1
                bee_size = detection.longest_side
                self.events.append(
                    {"frame": frame_index, "track_id": track_id, "status": status, "bee_size_px": bee_size}
                )
            source_ids = previous.source_ids + ([detection.source_id] if detection.source_id is not None else [])
            next_active[track_id] = Profile(track_id, current, status, bee_size, source_ids)

        for detection_index, detection in enumerate(detections):
            if detection_index in assigned_detections:
                continue
            track_id = self.next_id
            self.next_id += 1
            sources = [detection.source_id] if detection.source_id is not None else []
            next_active[track_id] = Profile(track_id, detection.midpoint, "New", None, sources)
        self.active = next_active
        return list(next_active.values())

