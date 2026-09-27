# Tracking distance is not an exception

The live servo integration exposed six false exception labels: two numeric image
distances repeated across three report copies. `decision_receipt_v4.py` recognizes
only a direct `servo_feedback.tracking.error` field, for matched raw/trimmed-fallback
tracking, with a finite numeric value in [0,1] and no unknown tracking fields. Such
entries become metric references instead of exception attention. Arbitrary numeric
errors elsewhere are not exempted. A matched claim is not proof of object identity.

The receipt additionally includes full servo_feedback records with original source
paths. This lets a reader see the measured delta, correction and local goal result
without another source lookup. Original reports, source hashes and terminal binding
remain unchanged. No runtime or live entrypoint was switched to v4 in this turn.

On the recorded successful servo, attention decreases from 15 to 9. Bracketed input
state, yield, continuation and servo-outcome schema attention remains. These need
separate typed presentation and consistency checks before suppressing them; this
candidate does not claim complete schema validation. The assistant reviewed the
new feedback section and remaining attention from the saved report, not a new live
episode. No full model receipt timestamp is available.

Ten negative controls cover strings, booleans, negative/out-of-range/null/NaN
metrics, lost status, an unknown tracking field, nested exception and numeric error
outside tracking. A preserved actual interruption still requires review. The first
probe mutated only one duplicate report copy, so some attention could come from
binding mismatch. Version 2 synchronizes every copy and explicitly requires valid
binding for all JSON-compatible cases; those tests also pass. NaN retains attention
and fails strict binding serialization. The initial weaker test remains archived.

Evidence: `results/receipt-metrics-01/` and `results/receipt-metrics-02/`, with source
hashes and generated receipts. The second cohort is authoritative for the consistent
copy controls. This narrow classifier does not validate every required tracking
field or reason/status relationship; generic servo-event attention remains present
even for an internally inconsistent matched claim.

The exact JSON serialization used for measurement grows from **5517 to 7323 bytes**
because full feedback records are now included. This is a semantic correction and
an explicit review-content tradeoff, not compression, fewer model tokens, reduced
cost or demonstrated lower end-to-end latency. Next consolidate repeated metric
references and add typed concise summaries for the existing servo/input-state
records while preserving negative evidence, then compare actual review work on a
fresh episode. Do not eliminate warnings merely to obtain a smaller count.
