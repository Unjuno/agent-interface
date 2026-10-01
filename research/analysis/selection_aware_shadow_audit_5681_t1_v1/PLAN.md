# Selection-aware shadow audit T1 — finite construction

## H — hypothesis

On a finite labeled capture frame, delivered-only prevalence can diverge from full-frame truth under event-dependent suppression, while an exact positive-inclusion-probability shadow estimator recovers the target in design expectation. A label-independent selection null must calibrate in expectation. A target stratum with inclusion probability zero and a transient outside the capture grid must be explicitly not estimable.

## T — experiment

Issue #5681 T1; frozen design from Issue comment #5922739514. The finite frame contains four cases:

1. Event-dependent gate: N=8, four positive transitions suppressed with independent audit probability π=1/2, and four negative transitions delivered with π=1. Enumerate all 2⁴=16 audit draws.
2. Label-independent null: N=8, four positive and four negative labels; all units receive independent Bernoulli audit with π=1/2. Enumerate all 2⁸=256 draws.
3. Zero inclusion: four positive suppressed units with π=0 and four negative delivered units with π=1; refuse a numeric recovery estimate.
4. Out-of-frame transient: an additional labeled transition between captures is not part of the N=8 frame and is refused as not estimable.

The candidate exhaustively enumerates exact rational design probabilities and Horvitz–Thompson prevalence for every draw. The independent raw-only auditor re-derives the scenario frame and expectation without importing candidate code, validates all rows and draws, and applies nine corruption controls, including attempts to emit numeric estimates for the zero-support and out-of-frame cases. It consumes only the candidate JSON.

## D — decision

`METHOD_PASS_SCOPED` only if event-dependent delivered prevalence differs from full-frame truth; both positive-support cases have exact HT design expectation equal to truth; the null calibrates; π=0 has no numeric estimate; the transient is excluded/refused; the raw-only audit and all seven corruption controls pass. Any malformed or incomplete table fails closed. No T2 empirical or GUI claim follows.

## C — confounders

The synthetic table has exact full-source labels, so weighting is unnecessary for this construction's truth; the test checks estimator algebra and refusal boundaries, not practical efficiency. The null isolates selection independent of labels. Candidate/auditor implementation errors remain possible despite independent code and mutations.

## U — limitations

Hand-authored finite frame, independent Bernoulli design, exact labels; no temporal dependence, label noise, hidden state, real capture process, GUI, action authority, or empirical prevalence. It establishes neither GUI safety nor T2 empirical selection bias. T0 `HOLD_NO_ELIGIBLE_SOURCE` and prior A1 results remain unchanged.

## Execution controls

- Branch: `research/selection-aware-shadow-audit-5681-t1-20261001`
- Additive evidence path: `research/analysis/selection_aware_shadow_audit_5681_t1_v1/`
- Allocation request: `SELECTION-AWARE-SHADOW-AUDIT-5681-T1-ORB-20261001-01`, 2026-10-01 04:20–04:35 UTC; conditional on fresh #5085 arbitration and start gate.
- Cached image only; no pull/build/network; read-only source; separate candidate and (only after candidate exit 0) raw-only audit containers; one CPU, ≤512 MiB, bounded PIDs.
- Any drift, occupied/ambiguous lane, missing image/platform, or nonempty output path is STOP before invocation. No retry.
