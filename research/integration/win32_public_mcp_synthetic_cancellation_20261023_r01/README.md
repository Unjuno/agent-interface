# Public MCP synthetic cancellation and recovery composition — R01

**Run ID:** `AI-WIN32-PUBLIC-MCP-SYNTHETIC-CANCEL-20261023-R01`
**Classification:** local synthetic process-composition test; not a live experiment
**Base main:** `05340f6edc8818d166df0d75ddc1a357f6f74e6c`
**Implementation commit:** `2d8a6b897`
**Host/runtime:** Windows 10 build 26300, CPython 3.11.9

## Question and setup

Does the opt-in standard MCP caller preserve custody when a synthetic spawned
producer blocks behind a parent-owned start gate, then cancel it, retire the
exact producer, run the separately spawned recovery helper, and verify neutral
state through a separate observer process?

The test binds target generation before the simulated caller/model delay,
admits one operation with frozen obligations, starts the fake producer behind
its gate, and sets a shared synthetic `down` event only after authorization.
The public cancellation tool returns within its asserted 500 ms bound. A
separate recovery process clears `down`; another process reads the neutral
event and returns an operation/generation/recovery-bound receipt. The public
`interface_results` endpoint retains action and cancellation as separate
records.

## Result

Normal Python and optimized Python each passed the single composed test. In
both runs, cancellation reached `recovered`, the producer had an integer exit
code, the fake down-state was clear, the independent observer reported
neutrality, and `release_confirmed` was true for this synthetic state model.
The original action remained `running`; cancellation did not promote it to
task success. `task_success` remained null and replay remained denied.

The exact stdout/stderr transcripts are retained in [`raw/normal.log`](raw/normal.log)
and [`raw/optimized.log`](raw/optimized.log). [`CONDITIONS.json`](CONDITIONS.json)
records commands, modes, host, exclusions and source hashes. `SHA256SUMS`
covers this packet.

## Limits and decision

This establishes only Python process ordering around shared fake state. It does
not exercise Win32 APIs, `SendInput`, a desktop, an application task, or an
independent task-success oracle. The test cannot prove that Windows retracts an
accepted input event, that late DOWN is impossible, or that release is bounded
under blocked platform I/O. The 500 ms assertion covers only this local MCP
cancel response in this synthetic run; two interpreter-mode executions are not
a reliability sample. No WSLc or Docker allocation was inspected or consumed.
Keep native release and task success UNKNOWN pending their separate gates.
