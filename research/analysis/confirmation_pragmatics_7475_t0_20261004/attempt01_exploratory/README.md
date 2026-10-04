# Issue #7475 T0: synthetic wording-factor audit

## H/T/D/C/U

- **H:** For otherwise identical confirmation cards, a truthful continuation/completion frame may change inferred action status or authorization scope. This T0 does not test that human hypothesis.
- **T:** Build three synthetic cards (message send, file replacement, sandbox form submit), each with a neutral/framed sentence pair. Keep operation facts, explicit not-yet-performed status, target, payload, consequence, reversibility, evidence, layout, and controls byte-for-byte equal within each pair. Derive a factual answer key before examining wording. Execute the renderer model and an independent raw-card auditor; inject three card corruptions.
- **D:** `PASS_METHOD_SCOPED` requires all six cards to match the same fixed facts/key within each pair and the independent audit to reject target, status, and response-order corruptions. It must not be reported as H-support.
- **C:** Explicit status and action fields may dominate sentence framing. The audit cannot observe user interpretation.
- **U:** Synthetic English cards only; no people, UI, accounts, model, or dispatch. Does not support any human-comprehension, approval, authority, or real action claim.

## Frozen scope and execution

Issue #7475, main `0178fd24e9c317fff40e0fa1952fbe7e8ae01078`. Synthetic names/payloads; the vendor is explicitly a sandbox. This is T0 construction auditing, not the separately approved/consented T1 human study.

Run from this directory:

```powershell
python run_t0.py
python audit_t0.py
```

Raw candidate cards are `candidate_raw.json`; independent recomputation and corruption controls are in `audit_result.json`. `SHA256SUMS` binds the inputs, scripts, outputs, and this report.
