# Issue #3814 — JSONL terminal-newline truncation

## H / T / D / C / U

- **H:** Removing only the terminal LF from a completed CLI JSON Lines response leaves syntactically valid JSON. A parser-only caller can misclassify a strict byte prefix as complete; a framing-aware caller can reject it and recover the exact retained report without dispatch replay.
- **T:** Allocation `issue-3814-jsonl-framing-formal-01`, branch `research/issue-3814-jsonl-framing-v1`, additive path `research/issue_3814_jsonl_framing_v1/`. Run current-main `runtime.cli_v1` once with a deterministic synthetic dispatch facade. Preserve full producer stdout, deliver exactly `stdout[:-1]`, compare parser-only and terminal-LF-aware handling, then use only `attempt-status`, `receipt --raw`, and `review` for recovery. Include complete-delivery, request-only, and pre-existing-directory controls. Independently audit raw bytes, hashes, attempt-file immutability, and dispatch count.
- **D:** `FAIL_FALSE_SUCCESS` if parser-only handling treats the valid-JSON no-LF prefix as completed. Independently report framing guard and read-only recovery predicates; they do not erase that failure. `FAIL_REPLAY_OR_RECOVERY` if recovery dispatches again or mutates retained request/report bytes. `HOLD_EVIDENCE_INCOMPLETE` for missing/unbound bytes or audit disagreement. `STOP_SETUP` for source/image/platform/container mismatch. One formal allocation; no retries or post-hoc edits.
- **C:** Docker Desktop `linux/amd64`; local immutable image `python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`; `--pull=never`, `--network none`, read-only source and fresh isolated output. Synthetic facade is the only dispatch implementation. No GUI, input, model/provider, or production code changes.
- **U:** One simulated downstream framing edge and synthetic CLI result only. No real pipe/network loss, model-visible delivery, task, power-loss guarantee, performance claim, broad reliability claim, or closure of #3711/#3808.

## Frozen source and command

Origin/main base: `de9eb00fb05dc98d71607742eb0c90a4f2c041a1` (fast-forwarded locally after confirming the intervening commits did not change `runtime/cli_v1` or `runtime/selector_v1`; related #3834 and #3711 research remains in its existing additive paths). The full runtime/CLI dependency closure is byte-frozen in `FREEZE.json` and checked in-container before formal execution.

Construction tests run separately before formal invocation. Freeze `preflight.py`, `runner.py`, `audit.py`, `test_runner.py`, this preregistration, relevant CLI source closure, image digest/platform, and Docker command in `FREEZE.json`. The preflight checks every listed source SHA and image/platform identity before it imports the formal runner. Formal output is written only to a fresh `evidence/formal-01/` directory. A separate container runs the frozen independent auditor read-only against that output.

No production behavior or previous allocation is modified.
