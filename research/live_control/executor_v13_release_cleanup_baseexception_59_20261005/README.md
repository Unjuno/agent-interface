# ExecutorV13 `release_all()` BaseException custody boundary

## H/T/D/C/U

- **H:** At PR #7635 head `61e5e877101f3182f64986406a5552917d554446`, the worker loop handles `BaseException`, but cleanup around `backend.release_all()` catches only `Exception`. A custody-bearing `KeyboardInterrupt` from cleanup can escape before terminal emission; an unrelated one must also re-raise only after a failed terminal is emitted.
- **T:** First run two frozen regressions against the exact parent. Then run the complete focused ExecutorV13 test module and actual release-backend composition suite on the candidate, plus an AST audit comparing the cleanup handler at parent and candidate.
- **D:** PASS requires parent red (both cleanup cases emit no terminal), candidate green (custody-bearing and unrelated `KeyboardInterrupt` both produce a failed terminal before propagation), backend composition green, and audit-confirmed custody preservation and deferred re-raise.
- **C:** A backend cleanup `Exception` already produces a failed terminal; the missing boundary is specifically a non-`Exception` subclass during cleanup. The change must not swallow process-level interruption.
- **U:** Deterministic Python construction only. No game, model, GUI, native input, latency, task-effect, or live allocation. The one OrbStack inspection STOP is recorded in the sibling `baseexception_release_custody_59_20261005/docker-stop.txt`; no container was started or retried.

## Frozen identities and commands

- Parent commit: `61e5e877101f3182f64986406a5552917d554446`.
- Candidate source snapshot SHA-256: see `SHA256SUMS` for `candidate-executor-v13.py`.
- Runtime: see `python-version.txt`.
- Parent red command: `python3 -m unittest research.live_control.test_executor_v13.ExecutorV13Tests.test_release_all_base_exception_with_custody_publishes_failed_terminal_then_reraises research.live_control.test_executor_v13.ExecutorV13Tests.test_release_all_unrelated_base_exception_publishes_failed_terminal_then_reraises -v`.
- Candidate ExecutorV13 suite: `python3 -m unittest research.live_control.test_executor_v13 -v`.
- Backend composition: `python3 research/doom/test_release_backend_v3_actual_composition.py -v`.
- Source audit: `python3 research/live_control/executor_v13_release_cleanup_baseexception_59_20261005/audit.py`.
- Static checks: `python3 -m py_compile research/live_control/executor_v13.py research/live_control/test_executor_v13.py` and `git diff --check origin/pr-7635...HEAD`.

## Observed result

The two regressions failed on the frozen parent: both observed the escaping `KeyboardInterrupt` but found no terminal event (`StopIteration`), exit 1. On the candidate, the focused ExecutorV13 suite passes 11/11, the actual backend composition suite passes 10/10, and the AST audit passes. The two added regressions verify delivery custody in the failed terminal and verify that an unrelated `KeyboardInterrupt` still propagates after terminal emission. `py_compile` and `git diff --check` pass.

This closes only the synthetic `release_all()` terminal-custody boundary. The separate live threat-exposure, per-key timing, useful-feedback, bounded-recovery, and MAP01 gates remain open. The earlier sibling report preserves the now-integrated step-loop BaseException result as historical evidence; this report is the distinct cleanup-path follow-up.

Raw parent failure, candidate results, source snapshots, audit code/output, runtime identity, and hashes are retained here. Verify file bytes with `shasum -a 256 -c research/live_control/executor_v13_release_cleanup_baseexception_59_20261005/SHA256SUMS`.

## Later disposition (2026-10-05)

After this frozen parent/candidate run, PR #7635 advanced to `636f61941e3da887a1641e4399c2f0e3373a7974`. Exact source inspection shows it now catches `BaseException` around `release_all()`, records custody in the failed release object, defers propagation until after terminal emission, and includes positive-custody and unrelated-interrupt regressions. That supersedes the source repair from this experiment. The recorded parent red and candidate pass remain historical evidence; the current PR #7653 repair is redundant and will be closed as superseded, with this artifact retained on its branch.
