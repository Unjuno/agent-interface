# Issue #6331 — wake-fenced lease validity T0

## Result

`PASS_METHOD_SCOPED` for the finite synthetic clock/owner traces only. Allocation-03 completed one candidate invocation and one independent auditor invocation, each exit 0, zero retries. The independent auditor reconstructed 24/24 scenario-arm rows and rejected all four frozen mutation controls. Predecessor allocations 01 and 02 stopped before candidate start when `main` advanced after preregistration; both exact STOP records remain intact.

| Scenario | Current relative Lease | BOOTTIME deadline | Wake-fenced model |
|---|---|---|---|
| No gap | LIVE | LIVE | current generation admitted |
| Short wake | LIVE | LIVE | old generation blocked pending requalification |
| Long wake beyond 160 synthetic ns TTL | LIVE | EXPIRED | old generation blocked |
| Awake `now == deadline` | EXPIRED | EXPIRED | suppress |
| Wake notification missing/late | LIVE in current lease | EXPIRED in BOOTTIME arm | `UNKNOWN_WAKE_COVERAGE`, first action suppressed |
| Held marker, no ack | policy result remains model-only | policy result remains model-only | release requested; no release claim |
| Held marker + ack + fresh rebind | old current lease appears LIVE | old deadline expired | only fresh bounded lease admitted |

This demonstrates a counterexample in the specified model: a relative monotonic lease whose clock pauses over suspend can appear live after the suspend-inclusive authority horizon has elapsed. It also shows that the chosen wake-fence model fails closed on unknown wake evidence. It does not demonstrate that the host or OrbStack actually pauses `perf_counter_ns` over suspend, or that any real input is held/released.

Exact source/image identity, argv, exit streams, raw output, audit, and hashes are retained in `FREEZE_v3.json`, `results/formal-03/RUN.md`, and `SHA256SUMS`. See [Issue #6331](https://github.com/Unjuno/agent-interface/issues/6331).

## Limits

No real sleep/resume, Windows/WSLc/OrbStack clock characterization, wake callback observation, GUI, task effect, physical input, model, or product safety claim. T1 would require a separate disposable host/VM allocation and explicit authority; this T0 does not authorize or perform it.
