# Issue #8319 A04 — saved-data factorial analysis

A04 is a new, separately preregistered saved-data allocation after A03 stopped before analysis because its frozen output parent was absent. It reads only the exact immutable A01 400-row raw fixture; it does not rerun the candidate, A02 auditor, or A03 analyzer/auditor.

The registered outputs are the four cell summaries for development accuracy, fresh accuracy, and optimism; seed-paired `FULL - CONTROLLED` within updater; `CASE_PATCH - STRATUM_PATCH` within feedback; and per-seed difference-in-differences. Each vector reports exact rational mean, median, minimum, maximum, and sign counts. This describes only the finite authored fixture; no p-values or population inference are permitted. A01 remains `HOLD_AUDITOR_GATE_FAILURE`; A02 remains `PASS_AUDIT_ONLY`; A03 remains `STOP_ANALYSIS_INPUT_OR_CONTRACT`.

The analyzer and auditor are independent standard-library implementations. The frozen output directory is committed before either one-shot formal command; each command refuses an absent parent and an existing output. Run construction checks with `python3 -B -m unittest discover -s research/analysis/controlled_feedback_factorial_8319_a04_20261008 -v`. The exact formal commands and invocation counts are in `FREEZE.json`.
