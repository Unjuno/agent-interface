# Issue #5404 — typed resumption packet T0

## H / T / D / C / U

**H.** In a deterministic interruption/recovery state machine, a typed packet that binds execution/authority generation, evidence/target identity, and last-action receipt state can avoid stale continuation and duplicate non-idempotent effects while using fewer recovery steps than full replay on benign pauses. An opaque prose-like summary will fail at least one injected boundary.

**T.** Freeze a pure-Python/no-dependency oracle and three recovery policies: `OPAQUE_SUMMARY`, `FULL_REPLAY`, `TYPED_PACKET`. Exhaustively cross five interruption points (`before_action`, `during_observation`, `after_timeout`, `after_authority_change`, `after_handoff`), five fault conditions (`none`, `stale_evidence`, `authority_revoked`, `geometry_changed`, `duplicate_receipt`), and two idempotency classes. This yields 50 scenarios and 150 policy rows. Preserve each packet/context binding, action receipt state, decision, emitted-action count, unsafe-admission result, and recovery-step count. Independently replay raw JSONL in a separate auditor. No GUI/model/network/task input.

**D.** `PASS_TYPED_RESUMPTION_SCOPED` iff all 50 scenarios × 3 policies are present; typed-packet unsafe admissions are zero; stale evidence and geometry changes are re-observed/re-grounded before any new effect; revoked authority and unaccepted handoff fail closed; committed/unknown action receipts never cause duplicate non-idempotent effect; all invalidation/receipt controls are detected; packet recovery on benign pre-action pause costs fewer steps than full replay; independent audit and four mutation controls pass. Any unsafe typed admission or duplicate non-idempotent effect is FAIL. Missing rows, hash/schema mismatch, or audit disagreement is STOP.

**C.** The event/effect oracle knows the ground truth, replaying a prior action has fixed synthetic cost, receipt lookup is perfect, and successful re-observation/re-grounding identifies the same semantic target except where authority is revoked or handoff acceptance is absent. These assumptions favor clean finite classification and do not measure a real recovery system.

**U.** This is a small deterministic contract experiment, not a test of human interruption timing, real GUI drift, hidden effects, crash persistence, event-store completeness, wall-clock latency, or task completion quality. Step counts are fixture units, not time or token proxies. Packet integrity does not prove the external world stayed unchanged.

## Frozen artifacts

- Candidate/oracle and policy runner: `experiment.py`
- Independent raw-only auditor: `audit.py`
- Formal output: `raw/formal.jsonl`
- Audit: `raw/audit.json`
- Freeze hashes and exact container commands: `SOURCE_MANIFEST.md`, `EXECUTION.md`
- Formal allocation: `typed-resumption-5404-t0-orbstack-20260930-01`; one formal invocation maximum.
