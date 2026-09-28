"""BIDS inventory without guessing which event denotes awakening."""

from __future__ import annotations

from pathlib import Path
from collections import Counter
import json
import pandas as pd

RECORDING_SUFFIXES = (".edf", ".bdf", ".vhdr", ".set", ".fif")


def inventory(root: Path) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"Not a dataset directory: {root}")
    recordings = sorted(p for p in root.rglob("*") if p.is_file() and p.name.lower().endswith(RECORDING_SUFFIXES))
    events = sorted(root.rglob("*_events.tsv"))
    report = {"dataset_root": str(root), "dataset_description": None,
              "recordings": [str(p.relative_to(root)) for p in recordings], "events": []}
    description = root / "dataset_description.json"
    if description.exists():
        report["dataset_description"] = json.loads(description.read_text())
    for p in events:
        frame = pd.read_csv(p, sep="\t")
        labels = {}
        for column in ("trial_type", "value", "event_type"):
            if column in frame:
                labels[column] = dict(Counter(frame[column].fillna("<missing>").astype(str)))
        report["events"].append({"path": str(p.relative_to(root)), "rows": len(frame),
                                 "columns": list(frame.columns), "labels": labels})
    return report
