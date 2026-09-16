# Invariant receipt binding v1

Task `INVARIANT-RECEIPT-BINDING-20260916-001`, Issue #494.
Publication base `bc1f9d5e5b9829cfdeba58db1f821bb4accdfe45`. Premeasurement freeze `a283c1264e09b083964949e9c6b4bae555f22a26`.

Decision: **PASS_RECEIPT_BOUND_REQUIREMENTS_SCOPED**.

## Question

`effect_outcome_contract_v2` requires every declared post-compensation invariant, but a caller could author or narrow that requirement list after observing the outcome. This rung compares outcome-time authored requirements with a pre-effect task/effect contract receipt whose canonical SHA-256 is retained before the effect.

## Frozen mechanism

Every fresh SQLite case starts at `(primary=old, collateral=preserve)`, records a wrong direct effect, then executes compensation. `clean` restores both fields. `collateral_damaged` restores only primary and leaves collateral=`damaged`.

`posthoc_authored` consumes requirements supplied after the outcome; in the damaged stratum this deliberately omits collateral. `receipt_bound` reloads the pre-effect receipt, verifies its canonical identity, and uses its complete `{primary: old, collateral: preserve}` requirement set. Both arms inspect the same authoritative final DB state and independently marked evidence.

40 first outcomes: 10 repetitions x 2 policies x 2 scenarios; no same-ID rerun. Remote Git blob identities for experiment/audit/tests/plan matched local executed bytes exactly before measurement.

## Results

| Policy / scenario | Correct | Outcome |
|---|---:|---|
| posthoc / clean | 10/10 | compensated |
| posthoc / collateral damaged | **0/10** | false compensated 10/10 |
| receipt-bound / clean | **10/10** | compensated |
| receipt-bound / collateral damaged | **10/10** | compensation incomplete |

Receipt-bound total: **20/20**. Posthoc-authored total: 10/20. Overall across candidate and negative control: 30/40.

The discriminator is provenance, not richer post-state evidence: both arms retain primary and collateral evidence. The failure occurs because the posthoc arm is allowed to redefine which evidence counts after seeing the outcome.

## Interpretation

A typed compensation reducer should not accept an outcome-time requirement set as authoritative when task semantics were already fixed earlier. Required invariants should be bound to the task/effect contract (or another authoritative pre-effect receipt), and result evaluation should reference that receipt identity. This prevents outcome-dependent omission of a known invariant.

This still does **not** discover omitted dependencies. If the pre-effect receipt itself fails to name a real invariant, binding faithfully preserves an incomplete contract. Nor does a SHA-256 receipt authenticate an untrusted producer; it only makes the selected bytes immutable/identifiable within this fixture.

## Validation

- Prefreeze construction tests: 6/6 PASS.
- Formal independent audit: 40/40 evidence-integrity cases pass; task correctness 30/40 including negative controls.
- Receipt-bound task correctness: 20/20.
- Independent extraction: 124 formal files, mismatch 0; audit byte-identical.
- Replay tests: 6/6 PASS.
- Copied-evidence corruption controls: receipt identity, DB state, result label, and receipt-binding metadata mutations rejected 4/4.
- Formal measured ID reruns: 0.

## Scope / H-T-D-C-U

**H.** Post-outcome requirement authoring permits incomplete compensation to be laundered by omitting a failed invariant; pre-effect receipt binding prevents this in the frozen fixture.

**T.** 40 fresh local SQLite cases after remote byte-exact source/plan freeze.

**D.** RETAIN scoped receipt-bound requirement provenance; no production ABI promotion.

**C.** An equivalent authoritative contract/version system could provide the same property without this exact receipt representation.

**U.** Generated cooperative SQLite only. Required invariants are still authored, not discovered. No cryptographic trust model for the receipt producer, GUI/external service, network/distributed transaction, power-loss, performance or natural-rate claim.

## Next rung

The next unresolved boundary is **contract evolution**: if the authoritative task/effect contract legitimately changes after planning but before compensation, should the old receipt remain binding, or must compensation be evaluated against a causally authorized contract generation? This separates immutable provenance from legitimate semantic revision.
