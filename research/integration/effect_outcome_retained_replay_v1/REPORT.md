# Retained effect-outcome integration replay v1

Decision: **PASS_RETAINED_EVIDENCE_INTEGRATION_SCOPED**.

## Question
Can the merged typed effect-outcome reducer from PR #467 mechanically absorb the retained first outcomes from the phase-boundary experiment (#427 / PR #434) and compensation-history experiment (#450 / PR #454), rather than relying on separate experiment-specific result vocabularies?

This is a deterministic posthoc integration regression over retained evidence. It creates no new task effect and is not a new reliability sample.

## Inputs and identity
The reducer is the byte-exact merged `research/integration/effect_outcome_contract_v1/outcome.py`: SHA-256 `db0a9dfe31aa406dc0ceea2c13552be974226281eb0a33413bffe104e8b7e548`, Git blob `ac524de1c1aa975074139a9e930e6e34b7ed9d17`.

The replay consumes the exact retained `rows.json` bytes from the conversation raw-evidence archives:
- phase-contract 40 rows: SHA-256 `bd3a3830591cb9758015c7251091e1688c9f601be65ec86be9375b10374cdbe4`;
- compensation-history 30 rows: SHA-256 `621098e0319ae636e5e3b86676fbe9569769dc78c72c01bfd44f08a2aa67f987`.

Both hashes were independently re-extracted from their original `.tar.xz` archives and match the manifest-retained `measured/rows.json` bytes exactly.

## Adapter
The adapter changes no scientific state. It translates the two historical record schemas to the typed reducer inputs:
- stageable wrong -> `REJECTED_PRE_EFFECT`, no events, current=`old`;
- committed stageable/direct effect -> one `EFFECT` event carrying the retained effect value;
- compensation-history events -> the retained ordered `effect` / `compensation` events.

One historical vocabulary normalization is explicit: #427 used `EFFECT_CONTRADICTED` before compensation existed; a direct wrong effect with no compensation maps to the now-more-specific `EFFECT_CONTRADICTED_UNCOMPENSATED`. No other label is renamed.

## Result
All **70/70** retained first outcomes reduce to the expected current typed outcome.

Breakdown:
- #427: 10 `PUBLISHED_VERIFIED`, 10 `REJECTED_PRE_EFFECT`, 10 `EFFECT_VERIFIED`, 10 normalized `EFFECT_CONTRADICTED_UNCOMPENSATED`;
- #450: 10 `EFFECT_VERIFIED`, 10 `EFFECT_CONTRADICTED_COMPENSATED`, 10 `EFFECT_CONTRADICTED_UNCOMPENSATED`.

Six integration tests pass. Five are fail-closed controls: missing committed history, non-monotone history, final-state/history mismatch, effect history attached to a pre-effect rejection, and a wrong stageable publication are all rejected with `ContractError`.

The first repo-oriented reproducer construction exposed a Python 3.13 dynamic-import harness defect: a dynamically loaded dataclass module was executed before being registered in `sys.modules`. This occurred before publication and did not change the reducer, adapter semantics or the already established 70/70 result. Registering the module before `exec_module` repaired the reproducer; the final form again passes all 6 tests and 70/70 replay.

## Interpretation
The construction reducer is compatible with both retained evidence cohorts at their measured scope. This closes a concrete integration gap: the two experiments do not require separate ad-hoc runtime outcome semantics for their supported states.

It does **not** promote a production ABI. The reducer still intentionally refuses partial/collateral compensation, causal-compensation ambiguity, duplicate primary effects, concurrency and other states not covered by retained evidence. Issue #468 owns the active collateral-compensation experiment; Issue #15 owns broader causal lineage; Issue #24 owns retry/idempotency.

## H / T / D / C / U
**H.** One evidence-bounded typed reducer can reproduce the phase and compensation-history distinctions already retained in separate experiments.

**T.** Apply the byte-exact merged reducer to 70 exact retained first-outcome rows; compare to normalized retained labels; inject five unsupported/corrupted evidence controls. No live rerun.

**D.** `PASS_RETAINED_EVIDENCE_INTEGRATION_SCOPED`: 70/70 classification match and 5/5 fail-closed controls.

**C.** The adapter necessarily supplies operation class/phase from fields retained by the source experiments; it does not discover them. The one legacy-label normalization is explicit rather than inferred from text.

**U.** Two generated local domains only; no new GUI/model/game/network effect, performance or end-to-end token result. Collateral compensation remains owned by #468 and is outside this reducer's accepted state space.
