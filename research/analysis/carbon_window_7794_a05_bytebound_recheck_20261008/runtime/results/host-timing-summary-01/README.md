# Retained primary-use host timing

This is a retrospective measurement of the unchanged seed 991336 trial in
`../guarded-observation-refs-primary-01`, not a new allocation or a matched
performance comparison. The original independent six-task evidence remains there.

The read-only `runtime.integration_checks.host_timing` command binds event rows
to retained request/reply identities, reply hashes and caller-review receipts.
It rejects broken ordering, nonfinite/regressing clocks and mismatched identities.
An unfinished send or presentation remains partial even when transport close is
recorded. Multiple presentations and historical reviews retain their own times.
The tool neither sends input nor changes the recorded evidence.

For these 29 calls, first send to last reply spans 246,136.6832 ms. The sum of
send-to-reply intervals is 8,985.4609 ms; the intervening reply-to-next-send gaps
sum to 237,151.2223 ms. All presentation callback durations sum to 95.3938 ms.
The six entered-value review declarations were recorded 6,844–8,541 ms after
their respective sends. Exact unrounded values and input hashes are in report.json.

These boundaries do not isolate inference, scheduling, user-interface rendering,
first useful model-visible feedback or semantic understanding. Callback completion
is not model ingestion. A review receipt is a caller declaration, not an independent
semantic oracle. Calls 27–29 include historical reads and close; the 29-call span
must not be labeled time to task completion. Transport close is not GUI cleanup.

Decision: this trial does not justify a global reduction of application waits.
Most elapsed time lies between calls, so subsequent integration work should
evaluate avoidable decision/observation round trips with a fixed task and explicit
review boundaries. It must preserve review before consequential submission.
Actual model tokens/cost, comparable useful-feedback latency and human tempo
remain unmeasured. No new model, sensor, automatic action or runtime policy exists.

Run `python3 -O runtime/results/host-timing-summary-01/verify.py` from the repository
root to recompute from the original committed archive. The verifier reads only
named transport members into a temporary directory and never executes archived code.

Validation: 260 protocol and 106 harness tests passed in WSL. The five new timing
tests cover input immutability, distinct timing boundaries, order/clock/hash
corruption, partial send/presentation, repeated presentation, unpresented review,
and relay-ID reuse across local attempts. Full check logs and tested sources are
retained in checks.tar.gz with checks-manifest.json.
