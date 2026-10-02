# #5694 A04 — matched-capture phase contrast

Successor to the immutable A03 HOLD. This allocation used the same capture schedule `[10, 50] ms`, expiry `20 ms`, and observation horizon `60 ms` in both phase arms; cue onset shifted across the first capture. One native-Windows CPU candidate and one separate raw-only auditor ran once each, with no retries. The audit replayed 9/9 rows, rejected 5/5 corruption controls, and returned `PASS_METHOD_SCOPED`.

See `REPORT.md`, `RUN_RECORD.json`, `execution/formal-01/`, and `SHA256SUMS` for the result and full receipts. Scope is a deterministic synthetic measurement-method fixture only; no live-control, safety, or GPU claim.
