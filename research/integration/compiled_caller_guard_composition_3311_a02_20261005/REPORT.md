# A02 composition probe report

Experiment ID: `compiled-caller-guard-3311-20261005-a02`  
Status: `PASS_CALLER_ACCOUNTING_CONTRAST` for this deterministic construction probe only.

The probe composed compiled GUI adapters v1 and v2 with the repository's adaptive acquisition caller v3. Both arms consumed synthetic wrong-value observations through the caller's warm-reuse path. The v1 runtime used pixel-change completion and returned `TASK_SUCCEEDED` after the simulated submit action; the caller then invoked its synthetic independent-effect stub, recorded failure, and returned `TASK_NOT_VERIFIED`. The v2 runtime checked the exact-value predicate, returned `SAFE_YIELD` after one simulated action, and the caller returned `EXECUTION_INCOMPLETE` with reason `effect_failed`, delivery `confirmed_partial`, and no effect-scorer invocation.

## H/T/D/C/U

- **H:** The real caller v3 preserves a compiled runtime safe-yield as incomplete partial progress without invoking its effect adapter; when a pixel-only v1 runtime reports completion for the same synthetic wrong-value sequence, the caller can withhold task success after the effect adapter reports failure.
- **T:** One deterministic paired contrast used the actual source implementations for adapters v1/v2, compiled GUI core, and caller v3, with three synthetic rows for v1 and two for v2. The caller used its warm-reuse route, revalidated twice, and received zero model callbacks. The effect stub was invoked only for the v1 completion. A separate assertion-only auditor reconstructed the expected outer receipts from retained raw. Focused caller-v3 and adapter-v2 test suites ran as construction verification.
- **D:** The predetermined pass condition required v1 inner completion plus outer `TASK_NOT_VERIFIED` after a failed synthetic effect check, and v2 safe-yield after one simulated action plus outer `EXECUTION_INCOMPLETE/effect_failed`, `confirmed_partial`, and no scorer call. Raw reconstruction had to match these conditions. Both conditions passed.
- **C:** The effect oracle is a deterministic test stub keyed to the known false exact-value predicate, not a separately implemented scorer and not an application. The two runtime versions intentionally use different compiled predicates. All callbacks were simulated. This probe tests composition and accounting propagation, not a complete desktop task.
- **U:** No GUI or application was driven; OS inputs = 0; model requests = 0. No actual task effect, cold path, local repair/recovery turn, latency, cost, efficiency advantage, or population result was measured. The warm-reuse route omits source observation, coarse model, anchor acquisition, and anchor model stages. One synthetic pair cannot support broader performance or reliability claims. Input authority/release behavior here is represented by simulated callbacks and receipts only.

## Run history and evidence

A01 stopped as `STOP_OUTPUT_PATH_INVALID` because the runner attempted to construct a nested output path with `Path.with_name`. Its in-memory outcomes were discarded and preserved as `construction-attempt-01.txt`; they are not used in the result. A02 is a fresh repaired construction run with exclusive raw creation. It is not a formal allocation and does not authorize a live desktop or shared-container run.

The assertion-only reconstruction is in `runs/a02/audit.json`; the runner output and focused tests are in `runs/a02/test-output.txt`. The focused current-main suites passed 19/19. The source freeze and source blob IDs are recorded in `PLAN.md`; the source files are preserved under `source/`.

Environment: macOS 27.0.1 arm64, system Python 3.14.5; no container used. This package does not establish current GitHub state. Delivery to PR #7854 / Issue #3311 remains pending because the GitHub API returned HTTP 403 rate limit exceeded; no further write retry was made. The current live-test gate also remains unresolved: nine shared OrbStack machines were observed running and were not touched.

Later source revalidation: GitHub `main` was read at `17b9d8b20d01f097a2054694398168dc2bc12000`. All six relevant Git blob IDs listed in `PLAN.md` were identical at that head. This is a source-continuity check only; A02 was not rerun and remains pinned to its original preparation source.
