# MAP01 capture freshness: R151 and R152

Both first outcomes are retained. R151 failed the unchanged 20 ms outer
key-release bracket at **22.3277 ms**; R152 passed at **12.2353 ms**.
R151 passed 17/18 runner checks and R152 passed 18/18. Both passed independent
ammo 50 -> 49, same-generation input release, the two-second recovery horizon,
and capture-time/public-receipt joins. Both demo audits returned
`PASS_SCOPED_NO_RECORDED_FORWARD_COMMAND`. Neither graph was promoted beyond
`SAFE_YIELD/delivery_uncertain`. Both owned targets exited normally and durable
custody ended clear. Each packet retains 83 hash-verified files.

The repaired oracle was integrated in [PR #10253](https://github.com/Unjuno/agent-interface/pull/10253).
Runtime for both trials matches main `57a509795df1351f5165992d09a80cc7618f8254`.
Private research helpers were at `fdddf0ecf5c96ab9c9837b6c6af595f612680311`
for R151 and `45129ef5e0b05c086bede1d6f85c0675ec7f4d45` for R152.
The latter adds bounded send tracing, with seven normal/optimized local tests.

R151's exchange-to-helper interval was 7.9521 ms. R152 measured 2.3694 ms:
0.0187 ms before send, 2.2465 ms in send, and 0.1042 ms after send to helper
entry. R152 did not reproduce R151's long interval. These elapsed intervals
include instrumentation and scheduling; they are not pure transport latency.
The cause of R151's delay remains unresolved. Its failed result is not erased
by R152's success. No matched speedup or general latency guarantee is established.

`RESULTS.json` is selected derived evidence, not the complete raw packet.
Manifest hashes identify the preserved private source packets; hashes alone
do not establish their contents. No new inputs are sent by these documents.

## Remaining scope

This is a finite release/effect experiment, not completion of MAP01 or of
computer control. Arbitrary delayed effects and launcher custody continuity
remain open. [#57](https://github.com/Unjuno/agent-interface/issues/57) still
requires same-model, matched-condition, all-attempt token/latency/correctness
evidence. Further runs must test a concrete hypothesis rather than select
successful sub-20 ms samples. Preserve failed attempts in future comparisons.
