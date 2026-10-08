# Oracle-boundary swaps — Issue #6230 T0 successor-2

**Disposition: `PASS_METHOD_SCOPED` for this fresh finite method allocation.** The independent exact-row auditor matched all 28 outcomes and rejected all 8/8 frozen corruptions, including a paired execution-only intent mutation that preserves local `executed_intent == model_intent` but violates equality with the actual arm. This new scoped result does not erase, modify or retroactively repair the original allocation's `HOLD_AUDITOR_INTENT_EQUIVALENCE` in PR #6279.

## H / T / D / C / U

- **H:** An independently reconstructed paired-intent oracle-swap table can distinguish planted semantic-, observation-, execution- and joint-only classes and catch a cross-arm frozen-intent divergence.
- **T:** Seven authored cases × four arms; no model or external effects. Cases include the four boundary classes, ambiguous truth, answer leakage and reset/carryover. Exact raw-row truth table is independently authored in `audit.py`; the auditor does not import candidate source. Eight mutations attack denominator, outcomes, paired intent (while maintaining within-row equality), leakage, ambiguity, state carryover, safety and oracle-plan content.
- **D:** `PASS_METHOD_SCOPED` requires exact 28-row equality with the independent table; execution-only intent paired to actual in every case; execution oracle delivers exactly the model intent; the four outcome vectors are correct; ambiguous/leaked arms get no credit; reset identity matches; no bypass; and all eight mutations are rejected. All gates passed.
- **C:** All tasks/truth values are hand-authored and deterministic. The result validates only the finite accounting/audit method; no causal model headroom is estimated.
- **U:** Real task semantics, adaptive response, oracle sufficiency, oracle-to-deployable evidence gap, production actuator exactness, transfer, real effect scorers and human tempo are untested. No model, GUI or T1 claim.

## Retained result

| Case | `actual / observation / execution / joint` effect correctness |
|---|---|
| Semantic-limited | `0 / 0 / 0 / 0` |
| Observation-limited | `0 / 1 / 0 / 1` |
| Execution-limited | `0 / 0 / 1 / 1` |
| Joint-only | `0 / 0 / 0 / 1` |
| Ambiguous | `0 / 0 / 0 / 0` — all `UNDEFINED` |
| Answer leakage | `0 / 0 / 0 / 0` — leaked observation-oracle arms rejected |
| Reset/carryover control | `0 / 0 / 1 / 1` — clean initial-state identity; contamination injected only in audit mutation |

Candidate: one invocation, exit 0. Independent raw-only exact-row auditor: one invocation, exit 0, `PASS_METHOD_SCOPED`, 8/8 mutations rejected, zero errors. Retries/substitutions 0. Five pre-freeze construction tests passed. Candidate/auditor were not rerun after this formal result.

## Relation to predecessor

PR #6279 remains a separate draft retaining the original formal raw PASS plus overall `HOLD_AUDITOR_INTENT_EQUIVALENCE`. This successor is a new frozen allocation with its own source hashes, raw candidate, audit and decision gate. It shows the strengthened method fixture can detect the specifically identified audit defect; it does not change what the predecessor's auditor did or did not establish.

## Environment and scope

CPython 3.12.10 on Windows x64, standard library only, host CPU. Docker Desktop service is Stopped/Manual and engine status unresponsive. The authored finite method fixture has no container-dependent semantics; no engine/container/WSL/shared allocation, model, network, GUI, game, OS input or external task effect was used. Host-only is not container evidence. See [FREEZE.md](FREEZE.md), [RUN.md](RUN.md), raw JSON and `SHA256SUMS`.
