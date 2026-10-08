# Scorer feedback attribution T0 A02

## H / T / D / C / U

**H:** The retained scorer-wait construction stream contains positive/negative scorer events but no plan/actuation identity. Applying the frozen A01 attribution helper without inventing actuation intervals must preserve a positive event as `UNRESOLVED` with no intent token.

**T:** Verify hashes for the original raw record, original audit, scorer event stream, scorer sample stream, and frozen A01 helper. Parse the exact serialized samples/events and run the helper with an empty per-key interval set. Do not rerun the candidate process or mutate the historical package.

**D:** `PASS_SCOPED` only if the raw stream has exactly one positive useful and one negative event; both events are tied to exact sample timestamps; the original audit explicitly records no plan/actuation binding; and the positive event stays unresolved with no attributed token. Any false attribution, source drift, schema mismatch, or missing sample fails.

**C:** The retained test is a host scorer-wait construction, not a MAP01/controller run. Its events may be irrelevant to useful game feedback, and an unresolved result cannot characterize a real controlled episode.

**U:** This checks serialized scorer ingestion and fail-closed behavior only. It does not add an action timeline, measure feedback latency, establish causation, efficacy, safety, recovery, or MAP01 task effect. No live allocation is consumed or authorized.

## Immutable inputs

All input hashes, source-main identity, expected dispositions, and one-run rule are fixed in `FREEZE.json` before execution. A01's allocation and result remain unchanged.
