# Issue #5817 — cross-task obligation conservation T0

## H / T / D / C / U

- **H:** A task-status-only scheduler loses unresolved side-effect/release obligations and may admit dependent work or report completion incorrectly; global-wait blocks independent work; an obligation ledger conserves responsibility until independently verified terminal evidence or an explicit unresolved no-owner stop, while gating only overlapping/unknown-dependent work.
- **T:** Deterministic finite event replay of 11 authored histories covering delayed effect, child release, timeout/escalation, accepted/unaccepted transfer, target crash, verified resolution, failed compensation creating a new child, duplicate compensation, resource alias, and unknown footprint. Compare task-status-only, global-wait, and ledger+dependency admission over dependent and disjoint read-only next tasks. Independent oracle reconstructs obligations, owners, terminal evidence, and admission from event histories.
- **D:** `PASS_METHOD_SCOPED` only if every created obligation ID is conserved at every prefix as verified terminal, unresolved with one accountable owner, or unresolved explicit `NO_OWNER_STOP`; timeout, cancellation, transfer, escalation, inverse emission, or parent closure never discharge without valid independent terminal evidence; dependent/unknown work is blocked, truly disjoint read-only work proceeds, and all five corruption controls are rejected.
- **C:** Strict global wait may be simpler and safer when independent work is rare. Existing per-action-group receipts may already retain every obligation without a session ledger. Conservative footprints can under-admit.
- **U:** Fixture authors obligations and footprints; no real GUI effect, release, ownership, persistence/crash durability, hidden dependency, authority, safety, or user benefit is established. T0 cannot guarantee an external app's complete side effects.

## Frozen boundaries

Transfer changes accountable owner only; accepted transfer never reduces outstanding obligation count. Rejected or unacknowledged offers preserve the source owner; target crash uses the explicit fallback owner or records unresolved `NO_OWNER_STOP`. `EXPLICITLY_ESCALATED` is a routing state, not terminal evidence. A verified compensation may resolve only its bound target obligation; any emitted side effect creates a distinct child obligation. Unknown resource footprint yields HOLD. The candidate is a finite simulator, and the auditor is separately implemented; no personal data, model, live app, or runtime mutation is involved.
