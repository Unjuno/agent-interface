# Per-key occupancy expected-inventory construction A01

**Question.** Does the retained T0 per-key ledger reject an omitted action key, and does an expected-key inventory make that omission explicit without changing the accepted timestamp bounds?

**H:** The retained ledger will classify a two-key event set as `BOUNDED` even after deleting one per-key row, provided another row and the verified-empty receipt remain. A completeness-aware wrapper supplied with the predeclared key inventory `SPACE, W` will preserve the complete case and return `UNKNOWN` for the deletion.

**T:** Use the exact retained `ledger.py` and raw JSON from main `6cd70ad4bfad74e11658057bf024918bffb24add`. Compare the original two-key events and a deterministic mutation deleting only the SPACE interval. Run a candidate wrapper and a separately implemented auditor over both cases. This is a host-only synthetic construction check; no live input or shared resource.

**D:** PASS_METHOD_SCOPED iff baseline reports BOUNDED with original bounds, baseline also reports BOUNDED on the omission (demonstrating the gap), the wrapper reports BOUNDED only for the complete set and UNKNOWN with `expected_key_inventory_mismatch` for omission, and the independent auditor reconstructs both outcomes without importing candidate code. Any mismatch is FAIL; incomplete execution is HOLD.

**C:** The row deletion mutation directly represents a dropped per-key receipt. The wrapper could still be given an incorrect inventory; this check does not authenticate inventory provenance, real X server processing, application delivery, task feedback, recovery, MAP01 efficacy, or safety.

**U:** One deterministic two-key fixture; no rate, latency, reliability, live occupancy, task-effect, causal, or generality claim. Expected keys are a frozen fixture input, not derived from observed rows.

## Freeze

- Current-main reference at selection: `c99d93a2c81945f0946173e48247bdd49e32a02a`.
- Historical input source commit identified by the exact raw's `main_sha`: `6cd70ad4bfad74e11658057bf024918bffb24add`.
- Baseline source and raw SHA-256 plus candidate, auditor, and fixture hashes are in `SHA256SUMS.txt`, created before execution.
- Allocation: `MAP01-PER-KEY-OCCUPANCY-COMPLETENESS-A01-20261005`.
