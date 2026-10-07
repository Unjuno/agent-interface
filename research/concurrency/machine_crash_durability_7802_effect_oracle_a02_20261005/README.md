# Issue #7802 A02 — bind recovery classification to independent effect truth

This successor preserves A01 / PR #7803 unchanged and tests a narrower assumption exposed by rereading its model: an absent local effect marker is not itself an independent observation that an external effect did not occur.

## H / T / D / C / U

- **H:** With identical local effect-marker and completion-receipt bits, recovery may need a different classification depending on independently known effect truth. When that truth is unavailable, the safe result is `UNKNOWN_RECONCILE`, not `NO_EFFECT_CONFIRMED`.
- **T:** Cross three independent effect-oracle states (`OCCURRED`, `NOT_OCCURRED`, `UNAVAILABLE`) with the two local marker bits and add an untrusted-record control. Compare A01's bits-only classifier to an explicit-oracle candidate and separately written auditor. Mutate an unknown-truth row to `NO_EFFECT_CONFIRMED` as a negative control.
- **D:** `PASS_METHOD_SCOPED` only when all 13 rows match the oracle, `NO_EFFECT_CONFIRMED` appears only with independently confirmed non-occurrence and no contradictory record, and the auditor rejects the mutation.
- **C:** A specific local operation may have an independent durable effect record and a contract that proves no-effect from its absence. External GUI/network effects generally occupy another durability domain; this model does not establish one.
- **U:** Abstract decision table only. No filesystem, SQLite, VM, abrupt power cut, external action, or application-side oracle was exercised.

## Result

The same local bits `(effect marker absent, completion receipt absent)` were classified `NO_EFFECT_CONFIRMED` by the A01 bits-only rule in both the happened and did-not-happen cases, and also when effect truth was unavailable. The explicit-oracle candidate classifies the first and third as `UNKNOWN_RECONCILE`, and reserves `NO_EFFECT_CONFIRMED` for independently confirmed non-occurrence without contradictory records. All 13 rows pass the independent audit; the false-negative mutation is rejected.

This does not invalidate A01's result as a finite Boolean-state model. It narrows its interpretation: the `effect_durable` bit must be an independently trustworthy effect oracle before it can support a no-effect conclusion. A01 did not establish that premise. No retry is authorized by any row.
