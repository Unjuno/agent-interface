# Issue #6147 T0 A05 — non-identifying p→q terminal convergence

**Disposition: `PASS_METHOD_SCOPED` for the frozen two-state convergence fixture.** The independent raw-only auditor matched all three depth layers, tree counts, tree-set digests and optimum; it checked all 13 admissible safe words and rejected six explicit corruption controls.

The only resolved depth-2 policy is `p→q`. Both initial candidates produce the same output trace for every safe word through depth 2; the specified `p→q` moves C0 and D0 to the same current terminal state Z. Z has the single declared envelope `CURRENT_TARGET_ALLOWED`. The terminal decision is `ALLOW_SCOPED_EFFECT` within this authored machine, while `initial_identity_claim=false`. No initial-state identity was inferred from LEFT/RIGHT or hidden labels; neither occurs on safe histories. The separate unsafe probe `u` would emit LEFT/RIGHT, and the auditor explicitly injected and rejected an unsafe policy.

## Execution and limits

- Allocation: `AI-6147-T0-20261003-05`, distinct from A03/A04, no predecessor raw reused.
- Base main: `43f7cd88d91af05036fae2100ec4e155c59e105c`.
- Candidate `python3 -I candidate.py`: exit 0, once. Auditor `python3 -I auditor.py RAW.json`: exit 0, once. Retries/tuning 0.
- Three layers contain 1 / 4 / 13 policies; resolved counts 0 / 0 / 1. RAW is 7,816 bytes, SHA-256 `b63cbe02cb8b47c430ffeb32d946d187a8f890138f2c767a0f043242c2a08321`.
- Frozen protocol and H/T/D/C/U: [`PLAN.md`](PLAN.md), [`FREEZE.md`](FREEZE.md); process record [`RUN_RECORD.json`](RUN_RECORD.json).
- Host CPU / CPython 3.14.5 / standard library only. No OrbStack, container, model, GPU, GUI, network or physical input.
- This is a finite synthetic method result, not proof of real-GUI convergence, probe safety, current-state completeness, effect truth, authority, runtime, product safety, or T1 eligibility. A04's other post-probe controls and its distinct raw remain separate and unchanged.
