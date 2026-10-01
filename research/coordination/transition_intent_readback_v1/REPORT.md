# Durable transition-intent readback v1

Task: `COORD-TRANSITION-INTENT-READBACK-20260916-020`

Decision: **`PASS_DURABLE_TRANSITION_INTENT_READBACK_SCOPED`**

## Question

Can recovery recognize an already-applied logical transition after unrelated canonical metadata changes make whole-record bytes differ?

The predecessor established exact content-bound readback. This rung keeps one-use confirmation consumption, conservative UNKNOWN behavior, zero recovery replay/refresh, and GitHub content-CAS writes fixed. The changed mechanism is a durable `last_applied_transition` receipt whose identity contains the intent ID plus the exact from/to generation and confirmation identity.

## First outcome

| Case | Post-commit drift / receipt | Recovery result | Recovery writes |
|---|---|---|---:|
| exact bytes | note_revision 0->1 | `UNKNOWN_CONTENT_MISMATCH` | 0 |
| intent-bound | same note-only drift; receipt exactly matches requested g1->g2/rev1 intent | `ALREADY_COMMITTED_SELF` | 0 |
| same ID / different content | receipt is same intent ID but g2->g3/rev2 | `CONFLICT_INTENT_CONTENT` | 0 |

The exact arm first committed the requested g1->g2 transition, then changed only unrelated `note_revision`. The observed final blob differs from the frozen expected after-state, so whole-record equality cannot establish the already-applied transition even though the transition receipt itself remains unchanged.

The intent-bound arm executed the same transition and the same note-only drift. Its whole record also changed, but `last_applied_transition` remained exactly equal to the frozen requested transition content, so recovery can classify it as already committed without a replay or confirmation refresh.

The conflict arm demonstrates that a naked intent ID is insufficient. `intent-020-A` bound to g2->g3/rev2 does not match the requested g1->g2/rev1 transition and is classified as a content conflict.

Measured totals: five successful state writes, three classifier GETs, zero recovery refresh writes, zero recovery replay writes, zero retries.

## Interpretation

Whole-record equality is safe but can be unnecessarily strict when unrelated canonical fields change after a successful transition. A durable, content-bound transition-intent receipt provides a narrower recovery identity: recovery can ignore unrelated metadata while still requiring exact transition semantics.

This is a scoped false-UNKNOWN reduction result. It does not weaken the conservative rule for unavailable or ambiguous readback, and it does not authorize replay.

## Boundary

The fixture stores only one `last_applied_transition`. A later legitimate transition can overwrite that receipt, after which an older intent may no longer be recognizable even though it was applied. This result therefore does not establish bounded-history retention, append-only replay history, garbage collection, authenticated intent provenance, crash/power-loss behavior, simultaneous linearizability, distributed consensus, or external-effect exactly-once semantics.

## Next single question

Keep the content-bound transition receipt fixed and add only a second later transition before recovery of the first intent. Compare a single `last_applied_transition` slot against a bounded applied-intent history. Test whether the older applied intent remains recognizable without allowing same-ID/different-content collisions or unbounded retention.

`verify.py` is retained deterministic checking code. No independent execution is claimed.
