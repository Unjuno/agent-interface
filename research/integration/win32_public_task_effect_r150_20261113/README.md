# R150: public verification of a post-recovery task effect

One fresh native Win32 fixture run passed the queue/recovery discriminator and
attached its delayed counter effect through public `interface_verify_task`.
The verifier reported independent task success while the original action stayed
`recovered`, its own `task_success` stayed null, and replay remained denied.
This connects the [R149 boundary](../win32_native_queue_effect_boundary_20261113/README.md)
to the existing server-configured oracle path; it does not establish MAP01.

Source main: `a0e695fe8193e708e2f60accb2bd3c6c351d7d4a`.
Runtime tree: `24c84540abb65d56ed0646ea9a0889b51c4a7e67`.
CPython 3.14.2, native Windows, QueryPerformanceCounter, no model calls.
One exact owned fixture, one dispatch, no fallback cancel or replay.
The generation was first observed by a read-only preflight and independently
matched by the dispatch session. The server configured the oracle; the client
submitted only the exact action call ID, not a claimed success receipt.

The action sent A-down/up, then exceeded its four-second authority in a wait.
Automatic recovery verified release and a two-second horizon. The deliberately
filtered fixture kept the original input in its native queue. After terminal
plus the planned hold, normal dequeue produced one counter increment.

| Observation | Monotonic ns |
| --- | ---: |
| Authority expiry | 264263027785900 |
| Recovery horizon end | 264265067785900 |
| Recovery terminal observed | 264265167527400 |
| Counter effect | 264265834681200 |
| Oracle request | 264266443976300 |
| Fresh oracle observation | 264266448084900 |
| Oracle receipt received | 264266448631700 |

The effect occurred 766.8953 ms after horizon end. The oracle preserved that
event time separately from its fresh observation time. Its retained artifact
joins the exact call, operation, generation and source-byte hash. The original
action record was byte-for-byte equal as a parsed object before and after
verification. A task-effect result is not a claim that all future effects ended.

All 23 preregistered queue checks and eight public receipt/evidence joins
passed. Before launch, four protocol tests, two native-structure tests and two
receipt-join tests passed. The join's negative cases include wrong generation,
old observation time, altered evidence and changed original action. Earlier
oracle construction checks found and repaired unbounded file reading and
boolean/numeric counter confusion; those failures remain in the private D15
preparation packet. Registration-only tests used fake native components and
do not count as native horizon evidence. R150 is the single live composition.

The fixture exited normally, the runner returned zero, and final persistent
custody was clear at revision 384. No runtime, CI, host-wide input setting or
launcher-custody rule was changed for this evidence publication.

[PUBLIC_RESULT.json](PUBLIC_RESULT.json) contains explicit selected receipts,
the counter artifact, action records and audits. Only its artifact locator is
reduced to a filename; original private evidence is unchanged. Source copies
are `.py.txt` and are not automatic imports or test-discovery targets.
[INTEGRITY.json](INTEGRITY.json) omits private path/session locators while
retaining ordered file sizes and hashes. All 186 original files were read back
and verified. Full raw remains in private packet
`win32_public_task_effect_20261113_r150`; its manifest SHA-256 is
`02a444613bba726b75fd08bc375ae34324eba1b5ac23d2962f207bb008811d8b`.
Hashes do not replace the retained original data.

Remaining work: connect the same separation to a target-specific MAP01 effect
oracle and control path, then run the same-model/all-attempt comparison in
[#57](https://github.com/Unjuno/agent-interface/issues/57). This deliberately
filtered single fixture does not establish spontaneous late OS delivery,
application quiescence, general timing, reliability, or model efficiency.
