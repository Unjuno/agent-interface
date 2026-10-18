# Issue #8084 T0 A03 — diagnostic reliability under sampling noise

## H / T / D / C / U (frozen before execution)

**H.** The A02 fixed-matrix eligibility rule (`span >= 0.25 AND peak >= 0.70`) is an algorithmic gate, not an estimate of stable learner-specific confusability. Under finite repeated diagnostic trials, eligibility and selected-pair decisions vary with sample size. The diagnostic-reliability screen will quantify that sensitivity on known synthetic Bernoulli rates without changing A02's rule.

**T.** Generate four authored three-pair probability vectors: strong pair `[.90,.20,.20]`, margin `[.78,.52,.32]`, low-dispersion `[.68,.60,.55]`, and uniform `[.40,.40,.40]`. For each vector, diagnostic size `n ∈ {5,20,100}` per pair, and 500 fixed seeds, generate independent binomial counts. Candidate receives only opaque row IDs, `n`, and observed counts. It recomputes empirical rates, the unchanged A02 span/peak gate, and deterministic top-pair label. An independently implemented auditor alone receives the true vectors and verifies every generated count/decision, then reports activation, false-activation, missed-activation and top-pair selection frequencies. No schedule or outcome/held-out labels are exposed to the candidate.

**Frozen decision gates.** Method harness accepted iff all 6,000 rows are independently reconstructed, counts lie in `[0,n]`, candidate outputs exactly match the frozen gate/tie rule, and mutation controls reject a flipped gate, altered count, altered pair, duplicate row, and changed denominator. Diagnostic-support screen is `SUPPORTS_N_GE_20_FOR_CLEAR_STRATA` iff at both n=20 and n=100: strong and margin activation ≥0.80; low-dispersion and uniform false activation ≤0.05; top-pair accuracy among activated strong/margin cases ≥0.90. Otherwise `DOES_NOT_SUPPORT_CURRENT_GATE_AS_RELIABLE_AT_N_GE_20`. This is a finite synthetic threshold, not inferential calibration or a participant sample-size recommendation.

**C.** The probability vectors are deliberately clean and stationary; real confusion is nonstationary, dependent, and affected by semantics, accessibility, feedback, and prior experience. Results may be driven by the stipulated 0.25/0.70 thresholds.

**U.** No human learning, GUI, real confusion reliability, adaptive-schedule benefit, safety, accessibility, burden, or runtime result. It does not change A02 or establish a T1 allocation. Preserve A01/A02 unchanged.

## Execution boundary

One candidate execution and one separate auditor execution; network disabled, read-only source/input mounts, pinned local WSLc image `agent-interface/native-suite-wslc-a08:20261004`, one CPU, 512 MiB requested. Candidate mount is restricted to `candidate/candidate.py` and `candidate/observed_counts.json`; auditor-only latent rates remain outside that mount. Capture each stdout/stderr and exit code. WSLc host cgroup/swap warnings, if emitted, mean hard memory/swap enforcement remains unverified.

## Frozen generation

`SCORING.json` contains latent probabilities and expected positive pair indices and is auditor-only. `generate.py` deterministically emits 6,000 observed rows from `seed = 808403 + stratum_index*100000 + n*1000 + replicate`; pair-level random draws use a separate seed derived from that key. Candidate has no access to `SCORING.json` or this generator. Seed and all thresholds are fixed in this protocol before execution.
