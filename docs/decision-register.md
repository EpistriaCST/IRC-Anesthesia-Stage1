# Decision register — unresolved before any confirmatory run

Status: **UNLOCKED / NO DATA ANALYZED**. The cited preregistration governs. The listed omissions cannot be repaired retrospectively while retaining a claim of exact preregistration; date, justify and archive a prospective analysis addendum before examining study outcomes. A changed hypothesis or proxy family requires a new preregistration or explicitly exploratory labeling. Do not fill these fields using results from ds005620.

| Topic | Frozen document specifies | Decision needed before scoring |
| --- | --- | --- |
| Anchor | dataset awakening/response event, not BIS | exact event codes, timing, and handling of repeated/ambiguous markers |
| Control | stable sedation far from awakenings | operational sedation status, minimum separation, matching algorithm, within-subject selection, overlapping episodes |
| Windows | both 10 and 30 seconds | channel validity, artifact mask, boundary and overlap policy, handling wake-up movement artifacts |
| Preprocessing | no complete prescription | reference, montage, channel inclusion, sampling rate, filters, line noise, artifact rejection, interpolation, leakage controls |
| ρ phase | debiased wPLI-like and scalar edge/density summaries | frequency band(s), filter/Hilbert parameters, graph percentile and reference/null threshold, zero/negative handling |
| ρ directed | Granger/VAR family | multivariate vs pairwise, order selection, stationarity, direction and graph threshold, conditioning |
| ρ transfer entropy | optional if computationally feasible | estimator, lags, surrogate controls, feasibility ceiling declared before outcome inspection |
| γ VAR | local growth/expansion from fitted operator | lag, regularization, growth statistic, orientation and comparability |
| γ variance transfer | time-lagged cross-channel variance transfer | a mathematically specified estimator with leakage and amplitude confound controls |
| γ TMS | conditional on clean available segments | inspect dataset and document availability and cleanliness criterion |
| μ participation ratio | covariance eigenspectrum | window channel count, rank threshold, normalized sign/direction |
| μ correlation dimension | embedded trajectory estimator | embedding, delay, distance scaling, temporal exclusion and finite-sample reliability |
| μ PCA slope | reconstruction error curve | component range, normalization, fit method, expected direction |
| μ validity | at least 2 of 3 proxies agree in direction | how agreement is aggregated by episode/subject, missingness rule |
| A | majority-subject same sign and corrected group significance | subject-level estimator, correction family, test/permutation, alpha, direction and missing subjects |
| B | asymmetric pre/post trajectory controlling total and alpha power | trajectory comparison, depth adjustment, symmetry statistic, group test |
| C | interactions explain substantially more variance near transition | **dependent variable**, model/null, held-out design, margin for “substantially”, test and correction |
| D | approximate within-subject stability of k-like summaries | estimand, identifiability assumptions and stability tolerance; non-gatekeeping |
| Cross-duration | qualitative disagreement makes family uninstrumentable | explicit disagreement and multiple-family adjudication rule |
| Gate | A and (B or C); robust failure leads No-Go | rule for underpowered/indeterminate results and code-generated audit trail |

No dataset-specific decision is implied by candidate code in `src/`. In particular, the code's default alpha-band, VAR order and PCA fit are software examples, not registered parameter values. Criterion C is **not currently evaluable** because neither its outcome nor its threshold is defined in the frozen document.
