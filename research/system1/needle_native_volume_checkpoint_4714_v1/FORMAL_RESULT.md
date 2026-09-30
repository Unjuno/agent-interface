# Issue #4714 formal result

Allocation `needle-native-volume-checkpoint-6842731-6842733-6842737-v1`; frozen source and commands are in [`src/FREEZE.json`](src/FREEZE.json), SHA-256 `a47acfbab106c9cbe72d1a9384a6280bb1cdb81f7cbcc5fe6eae1b31216ba871`.

**Decision: `HOLD_LATENCY_BUDGET`.** One formal trainer run completed all three fresh seeds ×12 arrivals, and the independent auditor completed separately. Integrity passed: 72/72 matched snapshots/requests/predictions, actual final bind and Docker-volume checkpoint bytes matched, audit errors 0, corruption controls rejected 5/5. No retry, seed replacement, tuning or post-result extension.

| Seed | Bind request→ack p95 | Native volume request→ack p95 | Ratio | Bind durable commit p95 | Volume durable commit p95 |
|---|---:|---:|---:|---:|---:|
| 6842731 | 110.420 ms | 104.592 ms | 0.947 | 100.934 ms | 20.089 ms |
| 6842733 | 134.049 ms | 104.898 ms | 0.783 | 121.152 ms | 19.848 ms |
| 6842737 | 183.292 ms | 180.214 ms | 0.983 | 114.109 ms | 19.919 ms |

The native volume reduced durable-commit p95 on all three seeds, but did not meet the <=60 ms end-to-end gate or the <=0.5 paired p95 ratio. Thus the experiment does not establish a useful request→ack latency benefit. The held-out prediction stage and host scheduling varied substantially; stage metrics are in `formal/AUDIT.json`. This is local fsync+atomic-replace+readback evidence only, not power-loss testing, model adaptation quality, production durability, or runtime readiness.

Raw per-seed requests, snapshots, predictions, references and timings are retained in `formal/training/`; the independent report and copied final volume snapshots are in `formal/audit/`. Final native-volume snapshot SHA-256 by seed:

- 6842731: `dbadb69fb124dec7659ef26c81ba35d126cc09dfb09984c3fce1f51ac89c2012`
- 6842733: `1fc6ab84aaaa53c7fd34b0081d5068be4fb7ee65f1c494fa20e68ac931f8b99e`
- 6842737: `76b4fa2f1b2a4b52ca0e4db6cfc3c6954873a6c4e185080dd8aac63cec44268c`

The local named volume `unjuno-needle-native-volume-4714-v1` is retained for independent inspection; it has not been removed.
