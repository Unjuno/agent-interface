# Issue #5521 T1 — restart, contradiction, and expiry

## H/T/D/C/U

- **H:** A persisted, reversible ANERGIZED state can survive a process restart, refuse contradictory evidence from the same authority generation, reactivate only on fresh positive evidence, and expire without admitting an old proposal. It should reduce duplicate verifier work versus stateless rejection while retaining more safe coverage than permanent rejection.
- **T:** Deterministic finite-state simulator; policies are stateless reject, permanent reject, and reversible anergy. Replay a frozen event schedule with duplicate proposals, same-generation contradiction, JSON serialize/reload restart boundaries, fresh-generation positive evidence, expiry, stale replay, changed target, and a new proposal fingerprint. An independently implemented raw-event auditor recomputes admission/effect decisions. This host rung does not kill/relaunch a process; require that in the container reproduction.
- **D:** Scoped PASS only if an ANERGIZED candidate has no effect except through an explicit fresh-generation SAFE reactivation; contradictory or stale evidence cannot reactivate it; restart preserves state; expired fingerprints stay non-admitted; changed targets remain distinct; anergy performs fewer verifier checks than stateless policy and admits at least as many safe proposals as permanent rejection; mutation controls are rejected by the auditor. Any unauthorized effect or stale reactivation is FAIL.
- **C:** The fixture and policy are authored by the experimenter; a simpler policy may win under another event schedule or proposal identity contract.
- **U:** This is a host-executed toy simulator, not the requested Linux container run, a GUI test, a semantic identity study, a probe non-interference result, or production evidence.

## Freeze

- Issue: #5521, following its T0 comment requesting crash/restart, contradictory evidence, expiry, and independent replay.
- Base: 434a8dd3041631358ffe1a9286b47f6c78365ae1.
- Output path: research/experiments/issue_5521_anergy_t1/.
- No Docker/OrbStack invocation: #5085 has no exclusive CPU allocation for this lane. The host rung is construction evidence pending an authorized container reproduction.
- Network/model/GPU/GUI/input: none.
