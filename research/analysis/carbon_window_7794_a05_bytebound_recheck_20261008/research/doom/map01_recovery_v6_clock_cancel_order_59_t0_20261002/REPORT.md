# v6 clock/cancel ordering T0 — stopped on fake-backend defect

Issue: [#6228](https://github.com/Unjuno/agent-interface/issues/6228), successor to #59. Base: `14b81dd1f6853623a694266b98538f812847257a`.

## Preregistered question and disposition

The question was whether the frozen v6 synchronous `runtime_clock()` round trip after the planner timer, but before the cancel RPC, can extend an active fallback within its lease, and whether lease expiry bounds it otherwise. The preregistered scenarios were A (600 ms timer, 400 ms clock delay, 2,000 ms lease), B (600/1,600/1,500 ms), and a cancel-before-clock control C (600/400/2,000 ms).

Disposition: **STOP_HARNESS_CANCEL_NONCOOPERATIVE**. Do not interpret this as PASS or FAIL evidence about v6 cancellation latency. The candidate invocation ran once; no retry or repair was made under this allocation.

## Source and execution provenance

Five source blobs and their SHA-256 identities are listed in the preregistration and `raw_trace.json`; all five were independently re-read from the pinned Git objects and matched. The candidate harness was frozen at SHA-256 `BCD15464A9535703BBCFF23BD7E169D7FFC584ED7EF3EE61493AD7F4E1D97EF7` before invocation. It loaded the actual executor-v10 and Lease source directly from the pinned Git objects, compiled and executed in Windows host Python; no copied substitute executor was used.

Exact candidate command:

```powershell
python research/doom/map01_recovery_v6_clock_cancel_order_59_t0_20261002/run_experiment.py
```

One candidate invocation, one independent audit, zero retries. No game, GUI, model, GPU, network, or input was involved.

Docker Desktop was prioritized but unavailable: Windows service `com.docker.service` was Stopped; selected context was `desktop-linux`; `docker ps -a --no-trunc` remained pending beyond 15 seconds and `docker info` did not return within 10 seconds. No service or container state was changed. The preregistered fallback permitted this no-external-effect host CPU test.

## Raw outcome and audit

| Case | Cancel ordering | Timer→clock/cancel | Lease | Release from start | Terminal |
|---|---|---:|---:|---:|---|
| A | clock then cancel | 600 + 400 ms | 2,000 ms | 2,000.020 ms | expired |
| B | clock then cancel | 600 + 1,600 ms | 1,500 ms | 1,508.310 ms | expired |
| C | cancel then clock | 600 + 400 ms | 2,000 ms | 2,000.012 ms | expired |

Independent audit passed all source identity, scenario configuration, event-shape, and verified-release checks. It also detected the fatal test-construction defect: FakeBackend loops forever after `Lease.wait()` returns `True`, ignoring the cancellation signal. Consequently A and C did not terminate on cancellation; both ran to lease expiry. B also expired at its lease, as expected under a cooperative executor, but the defective control means it cannot validate the causal distinction. The only justified finding is that this fake does not exercise executor cancellation. The measured timestamps are retained solely as invalid-run raw evidence.

## H / T / D / C / U

- **H:** Unresolved; candidate conditions cannot be assessed because cancellation was not honored by the fake backend.
- **T:** Frozen-source load and syntax construction passed once; candidate ran once; independent raw-only audit ran once.
- **D:** Preregistered support gate not met. Typed stop is `STOP_HARNESS_CANCEL_NONCOOPERATIVE`; thresholds unchanged.
- **C:** The fake's event semantics are defective despite loading the real executor and lease. No causal statement about v6 behavior or production latency follows.
- **U:** No formal MAP01 allocation, live control, model, game effect, safety, efficacy, or product claim.

## Files

- `run_experiment.py` — frozen-source candidate harness; intentionally left unchanged after invocation.
- `raw_trace.json` — raw candidate events and source identities.
- `audit_trace.py` — independent read-only recomputation and stop classifier.
- `independent_audit.json` — machine-readable audit result.
- `SHA256SUMS` — package integrity manifest.
