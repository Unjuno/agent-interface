# ExecutorV13 release_all BaseException construction A01

## H / T / D / C / U

- **H:** If `backend.release_all()` raises a custody-bearing `BaseException`, ExecutorV13 must still publish exactly one failed terminal carrying the release failure and its batch-position custody, then propagate the original interruption.
- **T:** Invoke exact ExecutorV13 source against a deterministic fake backend. Its step succeeds; `release_all()` raises `KeyboardInterrupt` with one unknown per-position delivery record. Compare the frozen #7653 baseline to the follow-up candidate.
- **D:** Baseline is FAIL if the interrupt escapes before any terminal. Candidate passes only if one terminal has `status=failed`, `release.verified=false`, the exact custody, and the same KeyboardInterrupt still escapes.
- **C:** A stricter policy might intentionally leave the active slot occupied with no terminal for any interruption in cleanup. That policy would need to be explicit and preserve custody elsewhere; the current code does neither—the exception escapes with no terminal payload.
- **U:** Deterministic in-memory harness with stubbed base imports only. It does not exercise native release, X11, physical input, sink durability, or gameplay.

## Freeze and result

- Parent PR #7653 head: `03ecc45a3d635c11327f571d0cdd365abb52b950`.
- Baseline `executor_v13.py` Git blob: `054ed684898140315e2c843243ee2e6331310b10`.
- Follow-up branch: `fix/59-v13-release-all-baseexception-20261005`.
- Candidate `executor_v13.py` Git blob: `5e8bbdc2f69490bbf1f002761984c0a1a0a51a7d`.
- Candidate latest commit at test adjustment: `81e09c9ee518b3adc2bc4b8e754a47371214887e`.
- Candidate regression file blob: `ff8e796d72408fa4ebdd6814c4cb2907cbde401e` (see GitHub source blob in the PR after the final test commit).
- Windows CPython 3.11. Run command: `python -B probe.py <baseline-or-candidate-executor-source.py>`; audit command: `python -B audit.py`.

Baseline raw: `raw-baseline.json` shows `KeyboardInterrupt` escaped and `terminal_count=0`.
Candidate raw: `raw-candidate.json` shows the same interrupt escaped after one `failed` terminal with `verified=false` and the exact custody.
Independent saved-result audit: `audit.json` is `PASS`.

## Scope

No game, model, GUI, X server, OS input, container, formal allocation, or live-control experiment ran. The candidate fix is stacked on #7653 and remains unmerged. No physical release or task-effect claim is made.


