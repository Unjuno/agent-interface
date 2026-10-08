# #5013 formal allocation STOP — harness setup/runtime

Allocation: `broker-fake-child-boundary-4485-20260928-01`  
Branch: `research/broker-fake-child-boundary-4485-20260928`  
Status: `STOP_HARNESS_CONFIGURATION`  
Formal invocation: **consumed exactly once; do not rerun this allocation.**

## Frozen provenance

- Main base: `7eb56d16fd51e5852cfa77faa3395317f14beaa6`.
- Broker Git blob: `5734f54f318db9ac5e96b2bed6f6bed105ac39ff`.
- Cached image: `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, linux/amd64.
- Docker context: `desktop-linux`; `--pull=never --network none --read-only`, read-only source, fresh writable output, 0.25 CPU, 256 MiB, 32 PIDs, dropped capabilities, no-new-privileges.
- The frozen five source hashes matched in-container preflight. Construction syntax and unit checks passed 2/2; output was empty immediately before launch.
- Formal command was the single command recorded in `FREEZE.json`. No GPU was requested. The two pre-existing containers were not modified.

## Formal outcome

The runner completed seven case records, then the independent raw auditor returned exit 1 with status `FAIL_AUDIT` and 12 baseline audit errors. Overall formal Docker exit was 1. Raw SHA-256: `f5be8cdab7fafae5686a947dfdfec0e0017be956afec52272d5b570d56a8357e`. The output manifest covers 50 files; post-run SHA-256 and byte-count verification found zero manifest mismatches. All 8/8 copied-evidence mutation controls were rejected, which does not repair the invalid baseline.

Observed root causes:

1. The generated fake executable under `/tmp/fake-codex` returned `PermissionError: [Errno 13] Permission denied`. The frozen tmpfs mount did not grant executable access. The fake child therefore did not run for the normal, timeout, or queued cases.
2. Normal cases did not pass broker `--once`. After writing a PermissionError receipt, the broker remained in its serving loop and the harness's 5-second outer timeout killed it. The exit-0, exit-23, timeout, and missing-executable cases were externally killed; they do not establish the intended child outcomes.
3. The malformed JSON case exited 1 with `JSONDecodeError` and made no child call. The idle `--once` case was externally bounded with no IPC side effects. The queued case processed only lexical-first `a`, left `z` untouched, but the child failed to launch, so its expected success gate did not pass.
4. The runner reports exit 0 but its broad `BaseException` handler also wrote `runner.error.json` for normal `SystemExit(0)`; this is a logging defect. The formal auditor's `FAIL_AUDIT` is preserved as emitted.

## H / T / D / C / U disposition

- **H:** Undecided. The intended fake-child exit/timeout/unavailable semantics were not exercised as preregistered.
- **T:** One local Docker invocation, seven case records, no retries. Complete raw, per-case IPC, stdout/stderr, exits, audit, execution and manifest are retained under `formal-output/`.
- **D:** `STOP_HARNESS_CONFIGURATION`; not a scientific FAIL/PASS. The one-shot allocation is consumed; do not alter outputs or retry it.
- **C:** Evidence identifies a tmpfs executable-permission mismatch and missing `--once` on regular cases. The run is not evidence about successful fake child status propagation.
- **U:** No real Codex/provider/model/GUI/runtime behavior, authority, task correctness, performance, or product claim.

## Successor boundary

A fresh successor may change only harness execution plumbing: explicitly executable disposable fake-child storage and `--once` for each single-request case, while keeping the seven-case scientific conditions and broker blob unchanged. It must use a new allocation identifier and fresh output path; this STOP and its raw evidence remain immutable.

