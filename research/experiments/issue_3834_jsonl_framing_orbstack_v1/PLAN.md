# Issue #3834 — terminal-LF removal successor

## H / T / D / C / U

- **H:** The real current CLI emits JSONL with terminal LF. Removing exactly that LF produces syntactically valid JSON that a parser-only caller accepts, while a framing-aware caller rejects as incomplete and uses read-only attempt recovery without redispatch.
- **T:** Freeze current main `c215b11fc9609ec02810a22317c926374f399858`, CLI source closure, runner, independent auditor, construction tests, source validator, image digest/platform, expected byte relation and gates. After publishing all hashes to Issue #3834, make one formal OrbStack allocation with synthetic dispatch only. Capture producer-accepted bytes; relay exactly `accepted[:-1]`; compare parser-only and newline-aware decisions; recover the exact retained report via `attempt-status` and `review`. Run a raw-only independent auditor in a second container. Include full-delivery, invalid-prefix, request-only and occupied-directory controls.
- **D:** `PASS_FRAMING_GUARD_SCOPED` iff output ends LF, delivered payload equals the strict prefix with that single LF removed, parser-only JSON parse succeeds, framing-aware completion is false, report/status/review bind to the same retained bytes, recovery is read-only, dispatch remains one, controls pass, and the independent audit has zero errors. `FAIL_FALSE_SUCCESS` for framing-aware false completion or replay/mutation; `HOLD_EVIDENCE_INCOMPLETE` for ambiguous/unbound evidence or auditor mismatch; `STOP_SETUP` for source/image/engine mismatch. No retry.
- **C:** OrbStack Docker 29.4.0 Linux/arm64; pinned Python 3.12 slim image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; network disabled; read-only root/source; separate fresh output and bounded tmpfs; bytecode disabled. The dispatch facade is the only patched component. No model/provider, GUI, native input, external network, or production changes.
- **U:** One synthetic local JSONL framing boundary. Not an actual pipe/network drop, live task recovery, power-loss durability, broad reliability, or Docker Desktop/linux-amd64 parity. Does not close #3711/#3808.

## Source closure

The exact SHA-256 closure is in `FREEZE.json`; `validate_freeze.py` verifies it before both formal execution and independent audit. It includes CLI serialization, attempt persistence, review, receipt/image helpers and the imported selector/motor-state contracts, plus every experiment script and construction test. Freeze digest and runner/auditor hashes are posted to #3834 before the formal allocation.

Construction tests prove only the byte-framing distinction; they do not exercise the CLI or consume the formal allocation. Formal raw bytes and audit output are retained as separate files under `results/formal-01/`.
