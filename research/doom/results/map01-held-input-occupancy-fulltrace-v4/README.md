# MAP01 v38/v39 full-trace held-input occupancy bounds

## Result

The v4 candidate outputs cover every hold-step start in both immutable source
traces. The separate v5 raw-only auditor passes both outputs with zero errors:

| Trace | Started holds | Sum of per-hold lower–upper bounds | Intersections with model waits | Special rows |
|---|---:|---:|---:|---|
| v38 | 11 | 3,289.046–4,380.031 ms | 3,048.890–4,039.878 ms | none |
| v39 | 29 | 8,595.945–11,232.820 ms | 6,301.200–8,452.733 ms | one partial key admission / cancel-ack race |

The v39 `cover-4`, step 10 requested `Down + space`. `Down` admission began
before cancel, but its acknowledgement was timestamped **156.623 microseconds
(0.156623 ms)** after cancel receipt. `space` was never admitted;
there was no `keys_held` receipt or in-step observation. InputOwner verified
empty keys at the cancellation boundary. Its any-key interval is conservatively
`0–13.209 ms`; the positive lower bound is zero because no capture certifies
continued occupancy. This is an observed in-flight cancellation race, not a
claim that no input occurred.

## Relationship to prior held-input records (#6175 / #6198)

This is a separately versioned boundary extension, not a reproduction or
replacement of the prior reports. #6175 and its receipt successor #6198
retained 27 completed v39 holds plus one verified interruption (28 rows).
The raw event trace also contains a later-started `cover-4` step 10 whose
`Down` admission straddles cancellation and whose `space` key was never
admitted. V4 represents that start explicitly with zero positive lower bound
and a release-bounded upper bound; v5 independently audits all 29 starts.
The earlier allocations, their output files, and their dispositions remain
unchanged. The metric here is any-key occupancy / planner-wait overlap, not a
reinterpretation of the earlier requested-versus-owner-commanded totals.

In the aggregate, lower/upper bounds overlap with the declared model-wait
windows as shown above. Those intersections and the per-hold sums are
interval-censored descriptive totals, not exact physical key-up times. They
are not v38/v39 treatment comparisons: the stochastic gameplay trajectories
and model-authored actions differ.

## H / T / D / C / U

- **H:** complete traces could be reconstructed into conservative any-key
  occupancy intervals, including partial input acquisition interrupted by
  cancellation.
- **T:** run versioned full-trace candidates against immutable v38/v39 data,
  preserve each pre-candidate failure, then independently reconstruct both
  final reports and model-wait intersections.
- **D:** `PASS_FULL_TRACE_INTERVALS_SCOPED` for v4 candidate outputs plus v5
  independent raw audit: 11/11 v38 and 29/29 v39 hold starts represented;
  source hashes match; zero auditor errors; v39 partial admission is
  `[0,13.209 ms]`.
- **C:** absence of normal key-up timestamps forces interval bounds; cancel
  receipt can race an already-admitted input call. Key-down admission/ack is
  not proof of continued held state, nor is program completion a key-up clock.
- **U:** two retained stochastic episodes only. No live allocation, model,
  GUI, game, input, semantic effect, safety-rate, performance, causal, or
  human-tempo claim.

## Reproduction

Run the frozen construction suites:

```sh
python3 research/doom/test_map01_held_input_occupancy_v1.py
python3 research/doom/test_map01_held_input_occupancy_fulltrace_v2.py
python3 research/doom/test_map01_held_input_occupancy_fulltrace_v3.py
python3 research/doom/test_map01_held_input_occupancy_fulltrace_v4.py
python3 research/doom/test_map01_held_input_occupancy_audit_v5.py
```

The one-shot v4 candidate commands and v5 raw auditor command are retained in
the frozen manifests and run records. The v5 auditor output is `audit-v5.json`.
No candidate or auditor is to be rerun under those allocations.

## Preserved intermediate outcomes

The original v1/v2/v3 analysis attempts and v4 audit STOP remain unchanged:

- [`v2 freeze and candidate STOP`](../map01-held-input-occupancy-fulltrace-v2/FREEZE.md)
- [`v2 run disposition`](../map01-held-input-occupancy-fulltrace-v2/RUN_V2_STOP.md)
- [`v3 freeze`](../map01-held-input-occupancy-fulltrace-v3/FREEZE.md)
- [`v3 candidate STOP`](../map01-held-input-occupancy-fulltrace-v3/RUN_V3_STOP.md)
- [`v4 freeze`](FREEZE.md)
- [`v4 auditor STOP`](AUDIT_V4_STOP.md)
- [`v5 audit-only freeze`](AUDIT_V5_FREEZE.md)

The v4 candidate outputs were verified by the independently implemented
v5 raw-only auditor. The v4 auditor's omitted-boolean failure is retained and
was not rerun.

The v4 freeze's final line names a planned `audit.json`; the v4 auditor STOP
emitted no file at that path. The audit-only v5 successor's actual retained
output is `audit-v5.json`. This filename correction is documented here without
changing the frozen STOP or candidate/audit bytes.

## Environment

macOS arm64, Python 3.14.5, deterministic CPU-only posthoc analysis. The
shared Docker engine had another long-running container and no exclusive CPU
lane was assigned, so this work did not start, inspect or alter a container.
No container isolation or analyzer throughput benchmark is claimed.
