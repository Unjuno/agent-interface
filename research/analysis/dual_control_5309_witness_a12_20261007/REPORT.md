# Issue #5309 A12 — held-out effect semantics

## Formal disposition

**`PASS_HELDOUT_EFFECT_SEMANTICS_SCOPED`** under the frozen finite fixture. Candidate, environment and raw-only auditor each ran once in separate pinned containers. The auditor reconstructed 384/384 arm rows, reported zero errors, zero unsupported completions, and zero authority grants. The held-out topology's correct-prediction/affordable-preserving/no-prior stratum contained 10 cases: GENERIC_IG completed 7; WITNESS_AWARE completed 10; advantage +3.

The formal auditor did not independently recompute the expected policy choice for every row. A separate, post-outcome read-only reconciliation was therefore frozen and run once against retained bytes. It independently checked all 384 choices against the frozen policy, confirmed equal information gain, revalidated raw transitions/receipts, and compared strata/held-out counts to `out/audit.json`: policy mismatches 0, transition/receipt mismatches 0, all metrics equal. This diagnostic adds verification but is not a preregistered experiment and does not alter the original formal verdict or the 1/1/1 candidate/environment/auditor invocation count.

The misspecified stratum did not require zero WITNESS_AWARE completions. It contained 45 cases per arm; actual receipt-backed completions were GENERIC_IG 16 and WITNESS_AWARE 15. This is not an unsupported completion: independent receipts bind case, action, destination, effect identity, and source. Across the candidate hints, 47 completion hints lacked a corresponding valid receipt; all remained non-authoritative and were classified UNKNOWN.

## H / T / D / C / U

- **H:** With identical admitted action sets and equal predicted information gain, witness-aware choice would improve independent effect-witnessed completion over lexical generic choice on an unseen transition topology when its prediction is correct and a preserving action is affordable; prediction misspecification must not itself create completion authority.
- **T:** 192 cases across three seen transition families and held-out `lollipop5`; correctness/misspecification, budgets 0/1/2, and prior-witness controls; 384 rows for two arms. Candidate had no mount access to oracle, topology identity, or true transitions. Environment generated realized transitions and receipts; raw-only auditor compared them against separately mounted truth.
- **D:** All frozen gates passed: 384 exact rows, four distinct degree signatures, action admissibility/budget, no action after a prior witness, all derived completions supported by a correctly bound receipt, zero unsupported completions/authority, and strict +3 held-out advantage in 10 eligible cases. The postrun strata and hints are descriptive; they do not change the frozen gate.
- **C:** The deterministic authored fixture, candidate-provided predictions, costs, and lexical tie-break may favor the witness-aware arm. Only one topology family is held out; this is not broad generalization. An ordinary mandatory effect readback may make additional action ranking unnecessary.
- **U:** No learned predictor, natural GUI, live receipt producer, real side effects, calibrated cost/risk, latency, user, authority, runtime/product safety, or human-tempo claim. No empirical prevalence or generalization beyond this fixture.

## Relation to predecessor evidence

A04/A05/A07 infrastructure STOPs, A06 method FAIL, A08 scoped PASS, A09 infrastructure STOP, A10 count-gate FAIL, and A11 `FAIL_AUDIT_MISSPECIFIED_STRATUM_GATE` remain unchanged. A12 is a separate main-based allocation. It corrects the *prospective* semantic gate for this successor only: model correctness is a stratum label, while realized independently witnessed effect determines completion.

See `PRE_RUN.md`, `RUN_RECORD.md`, immutable `FREEZE_SHA256SUMS.txt`, the separate `POSTRUN_RECONCILIATION_FREEZE.md`/`POSTRUN_RECONCILIATION_SHA256SUMS.txt`, postrun `SHA256SUMS.txt`, and the two audit JSON files under `out/`.
