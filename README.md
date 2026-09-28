# IRC anesthesia: Stage 1 analysis scaffold

This repository is a **working scaffold**, not a completed or executable confirmatory analysis of human EEG. Its authority is Charles S. Thomas, *A Pre-Registered Two-Stage Empirical Program for Testing a Three-Surface Decomposition of Recursive Maintenance Cost in Anesthesia State Transitions* (1 March 2026), [DOI: 10.5281/zenodo.18828766](https://doi.org/10.5281/zenodo.18828766). Read the frozen document before changing any analysis choice. The repository cannot amend the preregistration.

Stage 1 asks whether three proposed surfaces can be measured in repeated awakening EEG: effective coupling density ρ, perturbation amplification γ, and dimensional conflict μ. The target is [OpenNeuro ds005620, version 1.0.0](https://openneuro.org/datasets/ds005620/versions/1.0.0), a propofol sedation dataset with repeated awakenings. The preregistration specifies 10 and 30 second pre-awakening, post-awakening, and matched stable-sedation control windows. Its Go rule requires criterion A and at least one of B or C. Stage 1 tests structural signatures, **not consciousness directly**. Stage 2 depends on a Stage 1 Go and a separate clinical study.

## Current status

The dataset has not been downloaded or analyzed here. The repository contains a dataset inventory command, a validated event/control manifest format, window extraction, illustrative implementations of several registered *families*, synthetic checks, and a decision register. **These implementations are candidate estimators, not locked operational definitions.** The registration names families but does not fix enough details to call output from this scaffold preregistered results. In particular, criterion C has no specified response variable or definition of “substantially more variance”; criterion D has no identifiable coefficient estimation procedure. The code therefore never returns Go/No-Go.

| Registered family | Current scaffold | Status |
| --- | --- | --- |
| ρ: debiased phase connectivity (wPLI-like) | debiased squared wPLI candidate | needs band, filter and scalar rule locked |
| ρ: directed Granger/VAR | pairwise lagged log residual-variance reduction candidate | needs lag, graph definition and confounding review |
| ρ: transfer entropy | absent | optional under registration, feasibility decision required |
| γ: local VAR instability | spectral radius of fitted VAR companion matrix candidate | needs lag, normalization and nonstationarity review |
| γ: lagged variance transfer | absent | registered required family, requires operational definition |
| γ: TMS evoked slope | absent | only if clean TMS segments exist |
| μ: covariance participation ratio | implemented candidate | needs direction and preprocessing locked |
| μ: correlation dimension | absent | registered required family, requires embedding/scaling definition |
| μ: PCA reconstruction error slope | implemented candidate | needs component range and slope definition locked |

## Getting started

Install Python 3.11+ and `python -m pip install -e .`; install `.[eeg]` if raw recordings require MNE formats. Run `python -m unittest discover -s tests -v` to check only the synthetic examples. Download the target dataset separately following `data/README.md`. Then run `irc-stage1 audit /path/to/ds005620` to inventory recording and event files, and inspect the event vocabulary before constructing a manifest from the example in `examples/episodes.example.csv`. `irc-stage1 measure --manifest <reviewed.csv> --output <candidate.csv> --duration 10 --band-low 8 --band-high 12` extracts candidate summaries; repeat with `--duration 30`. The CLI marks the outputs `EXPLORATORY_CANDIDATE`. It refuses invalid or overlapping windows and requires explicit control onsets. It will not guess an awakening event from a label.

The next useful contribution is an EEG analyst's written resolution of `docs/decision-register.md`, with decisions made before examining transition contrasts. A subsequent tagged code revision could implement both remaining required families and freeze all settings. Only then should a blinded run on ds005620 be considered for Stage 1. `docs/analysis-plan.md` maps the registered criteria to the missing execution steps. `CONTRIBUTING.md` sets out a focused audit request.

No human data, analysis results, claims of validation, or interpretive significance are included. Code is available under the MIT License; the registered PDF is separately marked CC BY-NC 4.0 and is linked rather than copied here.
