# ExecutorV13 release-custody BaseException boundary

## H/T/D/C/U

- **H:** At the exact #7635 parent commit, a `KeyboardInterrupt` carrying `release_batch_publication` can escape the `except Exception` handler before ExecutorV13 assigns failed status or carries custody into its terminal release record. The candidate must fail closed and preserve that ledger. An unrelated `KeyboardInterrupt` must still be re-raised after terminal cleanup.
- **T:** Run the focused ExecutorV13 test module and the actual release-backend composition test at the frozen candidate commit; independently inspect the parent/candidate worker exception handlers with `audit.py`.
- **D:** PASS only if both focused suites pass and the independent source audit finds the parent catches `Exception` only while the candidate catches `BaseException`, preserves the custody field, and retains an explicit re-raise path.
- **C:** Existing backend/Executor composition may already retain ordinary `Exception` failures; the residual may be limited to Python `BaseException` subclasses. A broad catch could also swallow unrelated interrupts, hence the no-custody re-raise test.
- **U:** Deterministic Python construction only. No GUI, game, model, native input, latency, task-effect, or live allocation evidence. The container attempt stopped before image identification because the local daemon returned an unsupported content-store error.

## Frozen identities and commands

- Candidate: `03ecc45a3d635c11327f571d0cdd365abb52b950` (PR #7653).
- Parent: `ddff6ebf8cea186accaae5dca98750ac16bb6a4b` (PR #7635 head at experiment time).
- Current `main` at inspection: `0eed302f7c2f821011154ce5d5ad23d6540d215d`.
- Runtime: see `python-version.txt`.
- Candidate tests: `python3 -m unittest research.live_control.test_executor_v13 -v`.
- Backend composition: `python3 research/doom/test_release_backend_v3_actual_composition.py -v`.
- Independent source audit: `python3 research/live_control/baseexception_release_custody_59_20261005/audit.py`.
- Static checks: `python3 -m py_compile research/live_control/executor_v13.py research/live_control/test_executor_v13.py` and `git diff --check origin/pr-7635...HEAD`.

## Observed result

Both focused suites pass 10/10 (20/20 total); the candidate passed py_compile and diff whitespace checks. The independent AST audit distinguishes the parent and candidate exception boundaries and checks for ledger preservation plus a re-raise path. Raw test output and source identities are retained beside this report. The container STOP is retained in `docker-stop.txt`; this is not a container PASS.

The current main and exact #7635 parent still catch only `Exception` in this worker boundary. The defect is distinct from #7635's regular-exception release-batch custody fix. PR #7653 remains stacked on #7635; hosted checks were queued at the latest check read. Do not merge this child before the parent and independent review.

## Reproduction

Run the three commands above from the repository root. `SHA256SUMS` covers the report, auditor, raw outputs, source snapshots, runtime and commit identities, and container STOP record.
