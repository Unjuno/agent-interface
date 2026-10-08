# MAP01 terminal-wait boundary — T5 container successor

Status: one-shot, CPU-only container transfer/reproducibility experiment. This does not run MAP01 or replay the consumed recovery allocation.

## H / T / D / C / U

- **H:** The frozen `JsonSession.wait()` can report an indistinguishable `TimeoutError("session event timeout")` for a wrong terminal ID, an absent terminal, and a matching terminal emitted only after the wait deadline. A pinned, isolated Python container should reproduce the already-scoped synthetic T4 protocol with the same raw event evidence and cleanup.
- **T:** On current main `c4d2d4b1ccf4512ec79af75bd8eaecfcada39947`, verify the immutable T4 candidate and runner Git blob IDs, run the four preregistered synthetic child cases once in cached `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (`linux/amd64`), network off, 1 CPU, 512 MiB, pids 64, read-only root/source, and a unique writable output mount. If candidate exits 0, invoke a separate raw-only auditor exactly once against read-only candidate evidence.
- **D:** `PASS_CONTAINER_TRANSFER_SCOPED` iff frozen source identities match; all four expected timing/ID cases are reconstructed from raw JSONL and satisfy T4's exact bounded predicates; the candidate/auditor IDs and retry count match this allocation; all child processes are reaped and reader threads joined; and independent audit exits 0. Otherwise retain the first outcome as STOP/FAIL/HOLD and do not retry.
- **C:** A source/hash mismatch, runtime/container setup error, Python/platform mismatch, scheduling delay, process cleanup failure, or auditor discrepancy can prevent a valid pass. Container transfer may itself change scheduling but cannot change the synthetic protocol's semantic scope.
- **U:** Synthetic `JsonSession.wait()` boundary only. This does not identify the lost original #3202/#3211 recovery-arm terminal cause, establish MAP01/game behavior, repair production code, or authorize another formal recovery run. CPU-only; no CUDA/GPU, model/provider, network, GUI, game, user data, or OS input. Docker/WSL uninstall/removal is out of scope.

## Allocation and immutable inputs

- Allocation: `MAP01-TERMINAL-WAIT-BOUNDARY-3211-T5-CONTAINER-20261002-01`.
- T4 predecessor: `research/doom/map01_terminal_sync_wait_boundary_3211_t4_20261002/`; immutable T4 candidate blob `afd5d4ea1bbbede29ecb67ff49f6e944b4d22320`.
- Runner: `research/doom/map01_recovery_cover_matched_v2_runner_3211_diagnostic_v2.py`; immutable blob `f5caf71a743a563b7de046b82d44db7ebe49e829`.
- T5 base main: `c4d2d4b1ccf4512ec79af75bd8eaecfcada39947`.
- Candidate invocation: 1; independent auditor invocation: at most 1 and only after candidate exit 0; retries: 0.
- Output namespace: `results/container-01/` (must be empty before the single candidate). The T4 `results/t4-01` path is never mounted writable or reused.

## Stop and record policy

Run construction tests and source/image/output preflight before candidate. Use exact image digest, no pull/build, `--network none`, no Docker socket, no GPU, no existing-container operations. Preserve any first candidate/audit outcome verbatim. A candidate nonzero/timeout means no auditor invocation. Record the exact disposition, invocations, raw sidecars, output digests and limitations on this package and Issue #3211. Keep #3211 open because the original recovery-arm event remains unobserved.
