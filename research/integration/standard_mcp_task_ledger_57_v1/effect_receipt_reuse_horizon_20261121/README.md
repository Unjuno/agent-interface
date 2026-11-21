# Effect receipt to reuse horizon composition (2026-11-21)

Base: a8402e9d8f74284e0bafd0aff3b55702f3dc4089 (current main at experiment freeze).

This packet records a narrow offline composition experiment. The merged effect receipt adapter output is inserted as C arm block 1 in the deterministic four-block A/B/C reuse-horizon fixture. The receipt task id is set to the final measured task id before adapter validation. Synthetic task, route, environment, model, and attempt-lineage identifiers are aligned to the frozen horizon fixture for evaluator compatibility; this does not claim the values came from one real matched workload. No production code or existing raw evidence was modified.

## Result

The corrected normal-mode pilot completed with exit code 0 and reports correctness-qualified token break-even at task 2 for both A and B. The integrated test covers timely, post-horizon, and unknown effect timing. All 33 tests across the effect adapter, comparison evaluator, and composition suite pass in normal and optimized (-O) modes. Case results are in results.json; raw stdout/stderr and exit codes are retained in raw-suite-normal.txt and raw-suite-optimized.txt.

The earlier pilot output is retained as raw-pilot-normal-pre-correction.txt but excluded: its receipt task id was changed after adapter verification when constructing the C horizon row. The corrected pilot and tests bind the same task id before adaptation.

## Environment

Initial tests stalled because Windows Python tempfile._get_default_tempdir blocked while probing inherited TEMP. raw-hang-traceback.txt retains the stack. run_local_tests.py creates a unique temporary directory under the isolated worktree, sets TEMP/TMP/TMPDIR before importing test suites, then cleans it up. The timeout records are preserved; the explicit-TEMP runs pass.

## Limits

All runs use synthetic offline fixtures. This validates the composition and attribution boundary only; it does not show live GUI/provider task completion, general efficiency or speed, recovery reliability, runtime distribution readiness, or research preview graduation. No PR was opened and no issue was updated.

Run from this directory with: python -u run_local_tests.py and python -O -u run_local_tests.py.
