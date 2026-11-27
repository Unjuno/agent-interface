# Repeated cancellation latency in the stopped-Calc MCP scenario

Eight fresh WSLc allocations were planned before execution, alternating four no-cancel and four cancel trials, executed sequentially. Each used main runtime code at `a97a0101edee41d38a3ae08e5e9fd5a5642a3837`, the same pinned image, one CPU, no network, private Xvfb and a fresh Calc/FODS fixture. The only intended condition difference is whether the existing runner requests cancellation after 500 ms; this delay starts after the pending response, not at the start of the internal wait. Every attempt is retained; none was replaced or excluded. These runs compare cancellation with a deliberately uncompleted 2 s wait, not two competing computer-control methods.

| Samples | Measurement | Min / median / max (ms) |
| --- | --- | --- |
| b01, b03, b05, b07 | Uncancelled fixed wait | 2000.074 / 2000.092 / 2000.160 |
| b02, b04, b06, b08 | Request timestamp to execution end | 5.073 / 8.266 / 10.370 |
| b02, b04, b06, b08 | Request timestamp to client terminal observation | 28.741 / 29.184 / 34.774 |

The client result loop polls every 20 ms, so client-observed delay includes polling and scheduling. Request time is recorded immediately before issuing the MCP cancel call on the same host monotonic clock. These four cancellation samples cannot establish tail latency, an SLA, reliability at scale, or a speedup against a conventional agent. They do not measure model tokens or task-completion economics. The controls show that the fixed wait actually elapsed when not cancelled; they are not evidence that a two-second wait was necessary for the task.

All eight executions ended as expected for their condition, verified neutral input release, and independently observed a blank file while Calc was stopped followed by the saved values 731 and 864 after resume. Thus cancelling the later wait does not undo already-sent save input. `python audit.py` checks input hashes, all eight conditions, call IDs, timing ordering, receipts and FODS values. It fails rather than silently excluding any missing or unsuccessful sample. The archives retain runners, input and top-level raw outputs; nested private receipt journals remain local and are represented by size and SHA-256.
