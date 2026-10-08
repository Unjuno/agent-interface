# Broker fake-child exit contract — OrbStack successor

This is a fresh seven-case experiment after #5013's immutable `STOP_HARNESS_CONFIGURATION`. It does not retry or pool that allocation. #5028's ARM64 exit-23 construction case remains a separate one-case result and does not count toward this matrix.

## H / T / D / C / U

- **H:** With an actual executable fake child and correctly wired `--once`, unchanged current-main broker behavior propagates child exits 0 and 23 exactly; emits typed fail-closed timeout/unavailable/invalid-instruction receipts; bounds an idle one-shot; and serves only the lexically first of two queued requests. Every receipt remains non-authoritative.
- **T:** One fresh OrbStack `linux/arm64` run with the frozen Python 3.12.14 image. Seven cases: exit 0, exit 23, timeout, missing executable, malformed instruction request, externally timed idle `--once`, and two queued IDs (`a-first`, `z-last`). The actual fake executable is written to a dedicated `exec` tmpfs and `chmod(0700)` is verified before launch; `/tmp` is separately `noexec`. Each normal broker invocation includes `--once`. A second isolated container independently audits only retained bytes and eight fixed corruption controls.
- **D:** PASS requires all seven expected process/receipt/response/child-count outcomes, `authority_granted=false`, complete source/input/output hashes and eight rejected corruptions. A contradictory complete matrix is FAIL. Missing raw/audit agreement is HOLD. Pre-run source/image/mount/runtime mismatch is STOP; consumed allocations are never retried.
- **C:** Frozen main broker only; deterministic local fake child; fresh private IPC per case; no real Codex/model/provider, credentials, network, GUI, OS input, or user data. Only the registered request/exit/availability/queue condition changes. ARM64 is explicit; no AMD64/Desktop parity is claimed.
- **U:** Seven fake-child cases on one OrbStack ARM64 host/image. This is evidence about the OS subprocess-to-broker boundary only—not live model behavior, runtime authority, GUI/task correctness, product readiness, or general cross-platform reliability.

## Execution and review

`FREEZE.json` and `SOURCE_SHA256SUMS` bind the target source and runner/auditor/test bytes. `run_cases.py` executes the cases and retains per-case IPC, receipts, responses, process status, invocation log, and a path/hash/length manifest. `audit_raw.py` independently reconstructs the matrix and challenges eight mutations without importing the candidate broker or runner. `test_audit.py` tests the audit logic on an authored synthetic fixture; it is not formal evidence.

Exact commands, image/runtime receipt, raw results, independent audit, scope-limited disposition, and local checks are retained alongside this README. No runtime source changes are part of the study.
