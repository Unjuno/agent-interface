# Admission-time scorer baseline barrier — A01

## H / T / D / C / U

- **H:** In the exact ExecutorV12 source at PR #7429 head `8fe1160c89cba797dacc235e28441d1660c13845`, synchronous completion of the `accepted` event emitter callback precedes `worker.start()`. A same-thread scorer sample in that callback can therefore finish after internal admission and before the first backend step.
- **T:** Run that exact source with a deterministic fake backend twice. First, delay completion of the accepted-event callback and verify the backend cannot start until a synthetic scorer-baseline callback finishes. Second, make the synthetic baseline callback raise and record whether submit leaves an internally busy executor with an unstarted worker.
- **D:** The candidate uses a frozen snapshot of `executor_v12.py` and its local import closure from the PR head. Wall-clock timestamps and thread identities are retained; event synchronization, not elapsed-time thresholds, determines ordering.
- **C:** For the success arm, baseline completion must strictly precede `backend.execute`; for the failure arm, no backend execution may occur and executor/worker lifecycle fields are captured. The auditor checks exact source hashes and rejects three mutated ordering/lifecycle records.
- **U:** This is host-Python deterministic construction with synthetic baseline callbacks and fake backend only. It does not call VizDoom, X11, a game, a model, physical input, a live recovery lane, or the formal allocation. It validates an integration seam and its failure boundary, not scorer values or task effect.

## Frozen inputs and execution boundary

- Base `main`: `a5f9d50135` (`origin/main` at freeze).
- Exact candidate source stack: PR #7429 head above; `executor_v12.py` plus seven required local-import files are in `source_snapshot/live_control/` with SHA-256 values in `SHA256SUMS.txt`.
- Candidate: `python3 candidate.py`, one execution.
- Audit: `python3 audit.py`, saved-record audit only.
- No retries. No external runtime or shared resource is used.
