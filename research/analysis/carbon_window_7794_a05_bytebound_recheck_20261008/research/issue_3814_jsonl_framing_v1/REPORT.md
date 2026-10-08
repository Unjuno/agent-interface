# Issue #3814 Docker Desktop formal-01 — result and audit hold

## H / T / D / C / U

- **H:** Removing only the terminal LF from the completed CLI JSONL output may leave valid JSON that a parser-only caller mistakes for a completed response; framing-aware rejection and read-only retained-result recovery should avoid replay.
- **T:** The one frozen `issue-3814-jsonl-framing-formal-01` allocation used a synthetic dispatch facade, actual `runtime.cli_v1` producer/status/receipt/review code, a simulated final-LF-only truncation, three controls, and an independent auditor in a separate local Docker container.
- **D:** **`HOLD_EVIDENCE_INCOMPLETE` (frozen audit gate).** The primary independent auditor passed 75/76 checks and returned HOLD because its request-only control expected exit code 0, while the current CLI intentionally exits 2 for `unknown_or_incomplete`. This was not edited or rerun after discovery. Independently from that defective gate, the raw evidence supports the preregistered `FAIL_FALSE_SUCCESS` observation: parser-only JSON decoding accepted the strict prefix as completed. Framing rejection and read-only recovery predicates passed.
- **C:** Docker Desktop Engine 29.8.0, Python 3.12.14, linux/amd64; pinned local image `python@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`; network disabled; read-only source; fresh local output. Formal base `de9eb00fb05dc98d71607742eb0c90a4f2c041a1`; current main later advanced to `5842cea6b16dde275f79caef3f09fdba828112e0`, with no changes to the frozen CLI/selector source closure.
- **U:** One synthetic response with in-memory removal of its final LF. No real pipe/network interruption, live model/task, GUI/input, power-loss, broad reliability, or platform-equivalence claim. This does not close #3711/#3808.

## Formal observation

- Producer exited 0 and emitted 268 bytes ending in LF (`ee7db911c9b00196c47ccffe104d8b2b3d8ae618aaec25acb94d2d860e2e1e91`).
- The simulated caller received exactly the 267-byte strict prefix without LF (`77a96d986f74c82330e9509828be057a5b3d3dd730e8b3a23d8d921f9a86b47d`). JSON parsing succeeded and the parsed payload said `completed`; the framing predicate rejected the absent LF.
- `attempt-status`, `receipt --raw`, and `review` each exited 0 and recovered the exact retained report SHA-256 `4f95fd5f395199f62ddaf9ada1571ea55abccb806709aad8d6a68ed9b179f3f2`. Request/report snapshots were byte-identical before and after recovery. Synthetic dispatch count was exactly one.
- Complete delivery and occupied-destination controls were consistent with the protocol. The request-only control correctly returned `unknown_or_incomplete`, `replay_allowed=false`, report missing, and exit 2.

## Why the independent audit is HOLD

The frozen auditor's `CONTROL_EXIT_CODES` check requires the request-only `attempt-status` return code to equal 0 (`audit.py`, check near line 90). The real CLI returns 2 for an unknown/incomplete attempt; this is directly covered by `runtime/cli_v1/test_attempt.py` (`main()` is expected to return 2 in the request-only child-exit test). All other 75 auditor predicates passed, including source hashes, container identity, raw-byte binding, one-byte-prefix relation, report digest, read-only recovery, unchanged files, and exactly-one dispatch. The auditor was not modified after formal execution, and the formal invocation was not repeated. Therefore the formal disposition remains HOLD rather than being promoted based on a corrected post-hoc gate.

## Provenance

- Preregistration and exact source/image freeze: `PREREG.md`, `FREEZE.json`.
- Construction and preflight stops: `CONSTRUCTION.md`.
- Formal runner artifacts and their original SHA256SUMS: `evidence/formal-01/`.
- Separate read-only container auditor output: `evidence/audit-01/AUDIT.json`.
- Formal invocation count: one. Construction/preflight attempts did not import or invoke the formal runner. No formal retries or evidence replacement.

The original Issue #3814 allocation had already been recorded as `STOP_SETUP` in an earlier GitHub comment. This is a separate successor allocation and preserves that history. The contemporaneous OrbStack/linux/arm64 result in PR #3846 is also distinct; this report adds Docker Desktop/linux/amd64 evidence, not parity.
