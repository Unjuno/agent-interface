# Issue #6133 T1c — WSLc measurement-gate successor

## H / T / D / C / U

**H.** A finite worker-aging measurement gate can (a) detect a planted joint RSS/latency slope, (b) reject cache-only and thermal-only controls, (c) preserve a single timepoint for each job's age and resource measurements, and (d) require old-generation receipt rejection only in cells where a restart actually committed, while never restarting across a pending obligation.

**T.** Generate five deterministic synthetic traces (`no_aging`, `monotone_leak`, `cache_plateau`, `thermal_only`, `hidden_state`) crossed with `NEVER`, `FIXED_AGE_10`, and `RESOURCE_THRESHOLD_112`, 40 jobs per cell (15 cells, 600 rows). Run only in one network-disabled WSLc container using the cached digest-pinned Python 3.12 image. Execute the construction suite, one candidate process, and one separately authored raw-only audit process, in that order. Candidate writes only to a separate output mount. No retry.

**D.** `PASS_METHOD_SCOPED` requires exact reconstruction of all 600 rows; leak detected in all three policies; no false aging classification in the other four traces; exactly one hidden-state output mismatch in the hidden-state trace per policy; coherent pre-restart age/resource timepoints; no restart with a pending obligation; every committed restart has a rejected prior-generation receipt; no-restart rows require no such receipt; and zero audit errors. Any missing/mixed-timepoint measurement, wrong classification, lost obligation, unsafe restart, or lineage error is `METHOD_FAIL`.

**C.** Synthetic deterministic metrics and a small fixed schedule; restart is modeled, not performed. Thresholds and policy labels are fixture constants, not calibrated production limits. The candidate and auditor share the frozen scenario specification but not implementation code.

**U.** No actual process aging, resource leak, host thermal confounding, X11 MCP session behavior, restart safety, task correctness, runtime benefit, or production policy claim. T0 previously found an optional persistent-session candidate but no qualified effect-safe restart path; this T1c cannot remove that HOLD.

## Relationship to the retained failure

This is a fresh successor, not a repair or rerun of T1b. T1b's `METHOD_FAIL_AUDIT` remains unchanged. T1b mixed post-restart age with pre-restart resource samples and over-required late-generation rejection in cells with no restart. T1c binds each job to `age_before` and measurements taken at that same pre-transition point; transition and post-state are separate fields. Receipt rejection is conditional on an observed generation transition.

## Runtime and safety

Source base: current main at freeze. WSLc is used because this is eligible single-container, CPU-only, no-network construction. Require the exact cached Python image digest, one CPU, requested 512 MiB, a read-only source mount, and a distinct writable output mount. WSLc's accepted memory flag is not treated as proof of hard memory or swap enforcement. Inventory containers before launch; do not touch unrelated workloads. No Docker Desktop/OrbStack, GPU, model, GUI, network, user data, native runtime, physical input, or external effect.

## Reproduction

From the repository root, mount this package read-only at `/src` and a fresh empty directory at `/out`, then run `python -B -m unittest -v test_audit.py`, `python -B /src/candidate.py /out/raw.json`, and `python -B /src/audit.py /out/raw.json` sequentially in the same pinned container. Exact command, image, status, raw hash, audit output and limits belong in `RUN.md` and `REPORT.md` after the one-shot execution.
