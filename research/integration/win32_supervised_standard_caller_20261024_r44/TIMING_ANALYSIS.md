# R44 post-hoc timing analysis

This addendum derives endpoint intervals from the frozen R44 `raw.json`, `task_raw.json`, cancellation trace, and server receipt. It does not alter those files, the original `SHA256SUMS`, or the frozen outcome. Reproduce with `python analyze_timing_r44.py` from the repository root. The run used the host's `time.monotonic_ns` domain. The frozen packet does not record the clock's reported resolution, so no numerical measurement-error bound is assigned. Values below are single-sample elapsed intervals, not distributions or confidence bounds.

| Interval | Result | Start endpoint | End endpoint |
|---|---:|---|---|
| Public observation call | 21.9831 ms | observation API call start | response returned |
| Screen capture | 1.5151 ms | capture start | capture end |
| Capture to observation response | 17.8439 ms | capture start | observation response returned |
| Artifact pipeline | 10.8745 ms | artifact pipeline start | artifact written timestamp |
| Public cancel call | 1.8725 ms | cancel invocation start | cancel response returned |
| Recovery Q-up send | 619.5432 ms | cancel response returned | exact recovery Q-up `SendInput` returned |
| Held callback after cancel response | 1,260.371 ms | cancel response returned | held hook callback returned |
| Phase-2 action execution | 46.1855 ms | server execution start | server execution end |
| Execution end to oracle observation | 244.1272 ms | server execution end | independent task-oracle observation timestamp |
| Execution start to oracle observation | 290.3127 ms | server execution start | independent task-oracle observation timestamp |

The phase-2 fixture effect is verified by the independent oracle, whose receipt is bound to the phase-2 call, operation, target generation, and oracle ID. The effect file has no write timestamp. Therefore 290.3127 ms is an execution-start-to-oracle-observation interval and an upper bound on when the effect was observed, not the physical effect latency. The terminal release/readback and task oracle are separate evidence. Runtime `task_success` remains null.

The timing supports only this R44 native-Windows fixture attempt. Each interval includes the work and scheduling between its recorded endpoints. The single sample gives no latency distribution, matched efficiency comparison, model/token accounting, MAP01 result, or real-application transfer. Clock resolution, endpoint instrumentation error, and OS scheduling uncertainty are not quantified by this packet.

Post-hoc manifest: `SHA256SUMS_POSTHOC_V1` hashes this analysis, its analyzer, and the original manifest. The original packet manifest remains unchanged.
