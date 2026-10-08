# #2802 application-event provenance / clock-domain result

Decision: **PASS_APP_EVENT_PROVENANCE_BOUNDARY_SCOPED**.

Allocation `app-event-provenance-2802-20260923-01`; formal1 / reruns0 / replacements0 / tuning0. Preformal remote freeze HEAD `c5ff47acb1bbd8bad1bc5f2c407e97e96a555e85` on branch `research/issue-2802-app-stream-provenance-20260923`.

## Result

All 18 fresh application-event child processes completed with exit 0 and the scoring-only private state transitioned `READY -> DONE` before each emitted `B` event.

| Scenario | n | Candidate | timestamp-only control |
|---|---:|---|---|
| SAME_DOMAIN_CONTIGUOUS | 3 | SATISFIED 3/3 | SATISFIED 3/3 |
| CROSS_DOMAIN | 3 | UNKNOWN_CLOCK_DOMAIN 3/3 | **SATISFIED 3/3** |
| GAPPED_SEQUENCE | 3 | UNKNOWN_GAP 3/3 | **SATISFIED 3/3** |
| REGRESSED_SEQUENCE | 3 | UNKNOWN_ORDER 3/3 | **SATISFIED 3/3** |
| CROSS_SOURCE | 3 | UNKNOWN_SOURCE 3/3 | **SATISFIED 3/3** |
| LATE_B | 3 | EXPIRED 3/3 | EXPIRED 3/3 |

The unsafe comparator therefore produced **12 unsupported ordered-success claims across 12/12 provenance-negative cases**. This comparator is a deliberately authored control, not an allegation about upstream production code.

Observed A→B numeric deltas were ~2.32–2.71 ms for prompt cases and ~40.53–40.70 ms for LATE_B against the frozen 20 ms source-time bound. In CROSS_DOMAIN, `CLOCK_MONOTONIC` A followed by `CLOCK_BOOTTIME` B happened to be numerically close enough that a timestamp-only comparison accepted all three cases; the candidate refused because the clock identity differed. Numeric proximity is not clock-domain equivalence.

Independent raw-only audit: `errors=[]`, all six cells ×3 present, candidate/oracle agreement exact, and **12/12 corruption controls rejected**. Seven policy units pass after the retained construction-only isolated-import failure. All frozen source SHA-256 values match after formal execution.

- RAW SHA-256: `1758bf82f0a9894de23cd307ca15e75c53269b30db5cdb1c3340e7635374461f`
- AUDIT SHA-256: `611ca58cb8ee8e1960bd244222f794e6b08ba9f2a5f0be2831afc353ffc4c151`
- SUMMARY SHA-256: `3cc4ade40120eea66c7b64574fc8c9a00040fd1b019ef11310e51462e9094a58`
- UNIT SHA-256: `fe836cbecd3b6b4f70bec51b58d30c3e45ad72ae7fb3cb63421a0f7337e651ae`

## H / T / D / C / U

**H:** ordered temporal success requires provenance in addition to a numeric timestamp: matching source, matching clock domain, contiguous increasing source sequence, and an in-bound event. Otherwise the result is typed UNKNOWN rather than success.

**T:** standard-library CPython 3.13.5 on the supplied Linux x86_64 execution container. Six directed scenarios × three cyclic repetitions. One fresh subprocess per case emits JSON events over a real stdout pipe and writes a private application state file before B. Actual Linux `CLOCK_MONOTONIC` and `CLOCK_BOOTTIME` readings are retained. No GUI, model/provider, task input, package installation or experiment network.

**D:** all frozen gates pass: 18/18 rows and exits/effects; exact candidate dispositions; all 12 provenance-negative cases expose the timestamp-only comparator; independent audit errors0; corruption controls12/12; source hashes unchanged.

**C:** both clocks are local Linux clocks and the host was not suspended; no drift or cross-host synchronization measurement follows. Stdout gives one producer process's stream order but not a distributed/global total order. The private file transition proves only the fixture effect, not causal necessity of an event or arbitrary application semantic completion.

**U:** dropped transport bytes, reconnect, wrap, multiple simultaneous obligations, malicious producers, cross-host clocks, GUI transfer, model usefulness, token/latency benefit, task correctness, action authority, reliability rates and production runtime integration remain open.

## Integration meaning

Allocation02 already showed that same-timestamp co-occurrence and later event order differ on a complete X11 channel. This allocation adds an independent application-stream constraint: **ordered temporal results must bind the source and clock domain and must not bridge a missing/regressed sequence merely because numeric timestamps look plausible**.

This does not close broad #2802. Its remaining explicit gaps include dropped-event transport/reconnect behavior, simultaneous obligations, and broader application/GUI transfer. Component PASS is not product or integrated-runtime acceptance.
