"""Strict window geometry. Controls and event meanings must be reviewer-supplied."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd

REQUIRED = ("subject", "recording_path", "events_path", "anchor_onset_s",
            "control_onset_s", "episode_id")


@dataclass(frozen=True)
class Episode:
    subject: str
    recording_path: Path
    events_path: Path
    anchor_onset_s: float
    control_onset_s: float
    episode_id: str


def read_manifest(path: Path) -> list[Episode]:
    frame = pd.read_csv(path)
    missing = set(REQUIRED) - set(frame.columns)
    if missing:
        raise ValueError(f"Manifest columns missing: {sorted(missing)}")
    if frame.empty or frame[list(REQUIRED)].isna().any().any():
        raise ValueError("Manifest must contain complete episodes")
    if frame.duplicated(["subject", "recording_path", "episode_id"]).any():
        raise ValueError("Duplicate episode ID in a recording")
    episodes = []
    for row in frame.itertuples(index=False):
        def resolve(value):
            p = Path(str(value))
            return (p if p.is_absolute() else path.parent / p).resolve()
        ep = Episode(str(row.subject), resolve(row.recording_path),
                     resolve(row.events_path), float(row.anchor_onset_s),
                     float(row.control_onset_s), str(row.episode_id))
        if not np.isfinite([ep.anchor_onset_s, ep.control_onset_s]).all():
            raise ValueError(f"Non-finite times for {ep.episode_id}")
        if not ep.recording_path.is_file() or not ep.events_path.is_file():
            raise FileNotFoundError(f"Missing input for {ep.episode_id}")
        episodes.append(ep)
    return episodes


def bounds(ep: Episode, duration: float, recording_duration: float,
           other_anchors: list[float], minimum_control_gap: float) -> dict[str, tuple[float, float]]:
    if duration <= 0 or minimum_control_gap < 0:
        raise ValueError("Invalid window duration or gap")
    t, c = ep.anchor_onset_s, ep.control_onset_s
    intervals = {"pre": (t - duration, t), "post": (t, t + duration),
                 "control": (c, c + duration)}
    for label, (a, b) in intervals.items():
        if a < 0 or b > recording_duration + 1e-9:
            raise ValueError(f"{ep.episode_id}: {label} outside recording")
    pre, post, control = intervals.values()
    if control[1] > pre[0] and control[0] < post[1]:
        raise ValueError(f"{ep.episode_id}: control overlaps transition windows")
    for marker in other_anchors:
        if control[0] - minimum_control_gap <= marker <= control[1] + minimum_control_gap:
            raise ValueError(f"{ep.episode_id}: control too near an awakening marker")
    return intervals


def cut(samples: np.ndarray, sampling_hz: float, interval: tuple[float, float]) -> np.ndarray:
    if samples.ndim != 2 or sampling_hz <= 0:
        raise ValueError("Expected channels × samples and positive sampling rate")
    start, end = (round(v * sampling_hz) for v in interval)
    if start < 0 or end > samples.shape[1] or end <= start:
        raise ValueError("Invalid sample interval")
    block = samples[:, start:end]
    if not np.isfinite(block).all():
        raise ValueError("Nonfinite samples; apply a prespecified artifact policy")
    return block
