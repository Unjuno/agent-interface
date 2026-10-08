# #6067 Linux per-deadline diagnostic construction

Disposition: PASS_DIAGNOSTIC_CONSTRUCTION_ONLY for D02 saved-data instrumentation; parent #6067 remains open. D01 launch STOP and auditor-v1 output-path failure remain preserved. No formal scientific allocation, GUI/cue acquisition, model/input/GPU or previous experiment rerun.

D02 executed once in isolated Linux Docker, pinned Python image `sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, networknone/read-only source/root, requested one CPU/128MiB total memory+swap/32PIDs. Exact observed container state/config retained. Guest CPU counters and cpu.max are raw observations, not proof of every isolation property. Monotonic absolute deadlines, 20ms period, ABCCBA blocks, 32 deadlines/block, 64/arm. Concurrent repository clone affected host load; no controlled causal ranking. Environment/clock/version and UTC times in output/run-d02/environment.json.

| Arm | Count | Median lateness (ms) | Maximum (ms) | >10ms | Bracketed wait CPU (ms) |
|---|---:|---:|---:|---:|---:|
| sleep |64|0.1094295|0.206024|0|14.267241|
| spin1 |64|0.000129|1.690247|0|72.757341|
| spin15 |64|0.000162|0.151460|0|965.618190|

Values are descriptive for this one serial block. Bracketed process CPU includes instrumentation overhead. Nanosecond timestamps are clock values, not calibrated measurement accuracy. No inference about tails, hard real time, general reliability or prior macOS 17.231ms lateness. Counter collection around waits cannot locate an exact descheduling event; use source-qualified tracing for that question.

Saved-only auditor independently recomputes count/order/deadlines/lateness and verifies CPU monotonicity plus scheduler/cgroup presence; omitted-row, altered-lateness and changed-arm controls rejected. Auditor v1 completed checks but failed writing inside the container-owned output directory (exit1). V2 changes only its output destination to a caller-owned path; saved raw unchanged, candidate not rerun. No claim of a second human/worker review.

Decision: retain diagnostic instrumentation as a construction reference, HOLD policy adoption. Required next step is original owner's separately frozen timing/resource requalification on the actual native capture host, then a distinct allowed T1 allocation. This Linux result grants no shared runtime or live authority. Main merge still requires FINAL-v5 non-author approvals and final integration check.

H/T/D/C/U is in PLAN.md. Source freeze hashes precede D01/D02; v2 output-only repair is separately hashed. Raw first outcomes are retained unchanged.
