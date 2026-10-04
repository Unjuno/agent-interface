# A04 summary-field audit mutation — A01

## H/T/D/C/U

- **H:** The A04 independent auditor may accept a corrupted `unique`, `ambiguous`, or `unmatched` summary in `RESULT.json` even when its detailed reconstructed rows and histogram remain unchanged. If so, the saved audit is incomplete for the result fields used to describe association ambiguity.
- **T:** Run the exact A04 candidate and original auditor from PR #7671 against its hash-pinned 634-event input. Make three isolated copies of the resulting JSON, changing only one top-level summary field per copy (`unique: 6→0`, `ambiguous: 33→0`, `unmatched: 0→39`). Run the original auditor and a separately implemented checker on each copy.
- **D:** The gap is reproduced if the original auditor exits 0 for any isolated summary corruption while the independent checker exits nonzero. The repair passes only if the pristine result passes and every isolated corruption is rejected.
- **C:** The auditor may intentionally verify only per-row classifications and candidate histogram, treating summary numbers as display-only. If so, the evidence report must avoid implying those top-level fields were independently verified.
- **U:** This is audit-integrity evidence for one deterministic posthoc software-record analysis. It does not establish true key identity, physical release timing, useful feedback, task effect, recovery, live control, or MAP01 performance.

## Freeze

- Current main at preparation: `52d2c7a7b6f4854d9d9de43d001a1d8ebfbfaacf`.
- Exact A04 parent at initial freeze: PR #7671 head `8150b0f67a2efe3c55aa006e1ca72415a23d1304`. The candidate, auditor, and input blobs were subsequently verified unchanged at PR #7671 head `4e75d82f262b12b7654d461781a72a623da58fb5`; the follow-up was then rebased onto the current stacked parent branch tip `3e46f325c8a3e3cc3f0961747c640ff9696327d9`. No candidate rerun followed these ref movements.
- Candidate source path/blob: `research/doom/map01_feedback_occupancy_join_a04_20261005/analyze.py`, `f23f29b93bb0a21f29aaa16b3424d782ed2eb5a2`.
- Original auditor path/blob: `research/doom/map01_feedback_occupancy_join_a04_20261005/audit.py`, `36e240ad0b593146ce98b7c570b834b8f260a152`.
- Input: `research/doom/results/v39-control-telemetry-gap-audit-20261004/events.jsonl`, SHA-256 `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`.
- Method: local CPython standard-library execution only; no container, game, GUI, model, network call from candidate, or input.
- Frozen repairs/tests: candidate once; original auditor once on pristine result; three isolated summary mutations each checked by both auditors; no retry of the source candidate.

## Result

PASS_AUDIT_GAP_REPRODUCED_AND_REPAIR_TESTED.

- The exact A04 candidate exits 0 and reproduces the pinned 634-event, 39-admission, 28-hold result with summary unique=6, ambiguous=33, unmatched=0.
- The unmodified A04 auditor passes the pristine result.
- Changing only unique, only ambiguous, or only unmatched leaves every detailed row and histogram unchanged. In all three cases the original auditor still exits 0 and writes pass=true; its own report summary remains recomputed from raw and correct, but it does not flag disagreement with the altered top-level RESULT.json summary.
- The independent v2 auditor passes the pristine result and exits 1 for each mutated result. On each mutation, the corresponding summary check is the sole failed v2 check. This follow-up now also repairs the A04 parent auditor itself: it derives `unique` / `ambiguous` / `unmatched` from independently reconstructed rows, requires exact integer values, and compares all three top-level `RESULT.json` fields. The repaired parent auditor passes pristine input and exits 1 for each isolated corruption.
- A separately implemented raw-output audit confirms the pinned input, 39/28 source counts, 6/33/0 reconstruction, exact one-field mutations, original-auditor false accepts, and v2 rejection. All seven independent checks pass.

This narrows the finding: the original audit independently computes a correct summary in AUDIT.json, but does not verify that the three duplicate summary fields in RESULT.json agree with those recomputed values. The candidate's row-level ambiguity result remains supported by the independently reconstructed rows; this is an audit consistency omission, not evidence that the 6/33/0 reconstruction is wrong.

## Commands and retained construction failures

- Python 3.11 targeted unit tests passed after rebase and repair: `py -3.11 -m unittest test_audit_v2 -v` from the package directory (4 tests; three isolated corruption subcases plus boolean-type rejection). Python 3.11 compilation of both auditors, the frozen candidate and original auditor passed before the runner; follow-up scripts also compile after rebase.
- The frozen runner executed the candidate once, the pristine audits, and three isolated corruptions; raw/RUNNER.exit.txt is 0.
- The separate raw-output audit returned PASS_RAW_OUTPUTS_RECONCILED, exit 0. The repaired parent auditor CLI passed pristine RESULT.json (exit 0) and rejected each of the three isolated summary mutations (exit 1); stdout, stderr, exit files, and reports are retained under `raw/PATCHED_PARENT_AUDITOR_*` and `raw/PATCHED_PARENT_AUDITOR_*.json`.
- git diff --check passed.

A later test invocation using a package path as a module name accidentally triggered repository-wide unittest discovery; it produced 21 passes and one unrelated `ModuleNotFoundError: check_workspace_index`. The package-scoped invocation above passed after rebase. The first shell redirection failed before Python because the raw directory was absent. The first runner start then stopped at STOP_AUDITOR_HASH_MISMATCH before candidate execution because the freeze contained a transcribed SHA typo. Both are retained separately; candidate execution began only after the corrected hash matched. An initial independent raw-audit verifier also failed because it expected the parent's audit JSON to contain status/errors rather than pass/checks. That verifier failure is retained in INDEPENDENT_AUDIT-RED.json and was corrected without rerunning the candidate or corruption cases.

The runner's RUN.json field started_utc is timestamped after its subcommands complete; treat it as a run-record timestamp, not candidate start time. No candidate start-time claim is made.

The checksum manifest covers the package and raw outputs except itself and manifest-verification logs. No live game, GUI, input, model, container, physical timing, true identity, application effect, recovery, or MAP01 claim follows.

## Construction history

The first PowerShell redirection stopped before Python because the raw directory did not exist. A second pre-candidate gate stopped on a transcribed auditor SHA mismatch. Both are retained in raw/STARTUP_PRECHECK_STOP.txt and raw/RUNNER.stdout.txt; candidate, auditor, and mutation counts remained zero. The copied file hash was rechecked and the freeze typo corrected before candidate start.
