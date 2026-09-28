"""Dataset inventory and explicitly non-confirmatory candidate measurements."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import json
import pandas as pd
import numpy as np

from .audit import inventory
from .metrics import summarize
from .windows import read_manifest, bounds, cut


def _load(path: Path):
    if path.suffix.lower() == ".npy":
        array = np.load(path)
        sidecar = path.with_suffix(".json")
        if not sidecar.exists():
            raise ValueError(f"Missing sample-rate sidecar: {sidecar}")
        meta = json.loads(sidecar.read_text())
        return array, float(meta["sampling_hz"])
    try:
        import mne
    except ImportError as exc:
        raise RuntimeError("Install optional EEG reader: python -m pip install -e '.[eeg]'") from exc
    ext = path.suffix.lower()
    readers = {".edf": mne.io.read_raw_edf, ".bdf": mne.io.read_raw_bdf,
               ".vhdr": mne.io.read_raw_brainvision, ".set": mne.io.read_raw_eeglab,
               ".fif": mne.io.read_raw_fif}
    if ext not in readers:
        raise ValueError(f"Unsupported recording format: {ext}")
    raw = readers[ext](str(path), preload=True, verbose="ERROR")
    raw.pick_types(eeg=True, exclude="bads")
    if len(raw.ch_names) < 3:
        raise ValueError("Fewer than three usable EEG channels")
    return raw.get_data(), float(raw.info["sfreq"])


def measure(args):
    episodes = read_manifest(args.manifest)
    grouped = defaultdict(list)
    for ep in episodes:
        grouped[ep.recording_path].append(ep)
    rows = []
    for path, group in grouped.items():
        samples, hz = _load(path)
        if samples.ndim != 2 or samples.shape[0] < 3:
            raise ValueError(f"Expected ≥3 channels × samples in {path}")
        for ep in group:
            event_table = pd.read_csv(ep.events_path, sep="\t")
            if "onset" not in event_table:
                raise ValueError(f"BIDS onset column missing: {ep.events_path}")
            onsets = pd.to_numeric(event_table["onset"], errors="coerce").dropna().to_numpy()
            if not np.any(np.isclose(onsets, ep.anchor_onset_s, atol=1 / hz, rtol=0)):
                raise ValueError(f"{ep.episode_id}: anchor absent from source events.tsv")
            all_anchors = [p.anchor_onset_s for p in group]
            intervals = bounds(ep, args.duration, samples.shape[1] / hz,
                               all_anchors, args.minimum_control_gap)
            for role, interval in intervals.items():
                block = cut(samples, hz, interval)
                values = summarize(block, hz, (args.band_low, args.band_high), args.var_lag)
                rows.append({"status": "EXPLORATORY_CANDIDATE", "subject": ep.subject,
                             "episode_id": ep.episode_id, "recording_path": str(path),
                             "role": role, "start_s": interval[0], "end_s": interval[1],
                             "duration_s": args.duration, "sampling_hz": hz,
                             "channels": samples.shape[0], "band_low": args.band_low,
                             "band_high": args.band_high, "var_lag": args.var_lag, **values})
    out = args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Wrote {len(rows)} exploratory candidate rows to {out}. No Go/No-Go assessment.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit", help="Inventory BIDS recording and event files")
    audit.add_argument("dataset", type=Path)
    m = sub.add_parser("measure", help="Measure candidate proxies; NO confirmatory verdict")
    m.add_argument("--manifest", type=Path, required=True)
    m.add_argument("--output", type=Path, required=True)
    m.add_argument("--duration", type=int, choices=[10, 30], required=True)
    m.add_argument("--band-low", type=float, required=True)
    m.add_argument("--band-high", type=float, required=True)
    m.add_argument("--var-lag", type=int, default=1)
    m.add_argument("--minimum-control-gap", type=float, default=30,
                   help="Example safeguard only; requires a prospective matching rule")
    args = parser.parse_args(argv)
    if args.command == "audit":
        print(json.dumps(inventory(args.dataset), indent=2, default=str))
    else:
        measure(args)


if __name__ == "__main__":
    main()
