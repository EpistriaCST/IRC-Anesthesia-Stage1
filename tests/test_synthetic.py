"""Checks for calculation/geometry faults, not validation of EEG interpretation."""

import json
import tempfile
import unittest
from pathlib import Path
import numpy as np

from irc_stage1.windows import Episode, bounds, cut
from irc_stage1.metrics import (phase_connectivity, directed_granger,
                                fit_var, participation_ratio, summarize)
from irc_stage1.cli import main


class SyntheticChecks(unittest.TestCase):
    def test_window_geometry_rejects_controls_near_events(self):
        ep = Episode("s1", Path("a.npy"), Path("a.tsv"), 80, 10, "e1")
        self.assertEqual(bounds(ep, 30, 200, [80], 5)["pre"], (50, 80))
        with self.assertRaises(ValueError):
            bounds(ep, 30, 200, [30, 80], 5)
        with self.assertRaises(ValueError):
            bounds(ep, 30, 200, [80], 45)

    def test_exact_window_size(self):
        x = np.arange(200).reshape(2, 100)
        np.testing.assert_array_equal(cut(x, 10, (2, 5)), x[:, 20:50])
        with self.assertRaises(ValueError):
            cut(x, 10, (9, 12))

    def test_var_instability_response(self):
        rng = np.random.default_rng(8)
        x = np.zeros((3, 5000))
        for t in range(1, x.shape[1]):
            x[:, t] = .8 * x[:, t - 1] + rng.normal(0, .1, 3)
        _, radius = fit_var(x, 200)
        self.assertTrue(.7 < radius < .9)

    def test_directional_synthetic_coupling(self):
        rng = np.random.default_rng(11)
        x = np.zeros((3, 4000))
        for t in range(1, x.shape[1]):
            x[0, t] = .7 * x[0, t - 1] + rng.normal()
            x[1, t] = .75 * x[0, t - 1] + rng.normal(scale=.4)
            x[2, t] = rng.normal()
        g = directed_granger(x, 200)
        self.assertGreater(g[0, 1], g[1, 0])
        self.assertEqual(g[0, 0], 0)

    def test_phase_and_dimensionality_bounds(self):
        rng = np.random.default_rng(12)
        x = rng.normal(size=(4, 2000))
        matrix = phase_connectivity(x, 200, 8, 12)
        np.testing.assert_allclose(matrix, matrix.T)
        self.assertTrue(np.all((matrix >= 0) & (matrix <= 1)))
        self.assertTrue(1 <= participation_ratio(x, 200) <= 4)
        result = summarize(x, 200, (8, 12))
        self.assertTrue(all(np.isfinite(list(result.values()))))

    def test_cli_writes_only_candidate_rows(self):
        rng = np.random.default_rng(3)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            np.save(root / "example.npy", rng.normal(size=(3, 14000)))
            (root / "example.json").write_text(json.dumps({"sampling_hz": 100}))
            (root / "example_events.tsv").write_text("onset\ttrial_type\n80\tawakening\n")
            (root / "manifest.csv").write_text(
                "subject,recording_path,events_path,anchor_onset_s,control_onset_s,episode_id\n"
                "s1,example.npy,example_events.tsv,80,0,one\n")
            main(["measure", "--manifest", str(root / "manifest.csv"),
                  "--output", str(root / "candidate.csv"), "--duration", "30",
                  "--band-low", "8", "--band-high", "12"])
            import pandas as pd
            result = pd.read_csv(root / "candidate.csv")
            self.assertEqual(set(result.role), {"pre", "post", "control"})
            self.assertEqual(set(result.status), {"EXPLORATORY_CANDIDATE"})


if __name__ == "__main__":
    unittest.main()
