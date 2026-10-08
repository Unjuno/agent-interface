# Frozen app-server interruption probe

One preregistered Luna-low no-tool turn was interrupted immediately after its
matching `turn/started` notification.  The app-server acknowledged the single
`turn/interrupt` request and emitted `turn/completed` with status `interrupted`.
The server-reported turn duration was 37 ms; interrupt-to-ack was 20.772 ms and
interrupt-to-completion was 21.039 ms.  No agent message completed and the
driver marked the result ineligible as an answer.

No `thread/tokenUsage/updated` notification was emitted.  The audit records
this as absent/unknown, not zero.  The interruption was probably early enough
to precede model generation, so this allocation does not measure saved tokens
or prove mid-generation cancellation.  It does prove a clean typed lifecycle
that is unavailable through force-killing the current process wrapper.

The journal also shows ten MCP startup-status notifications between ephemeral
thread creation and interruption despite a no-tool base instruction.  Thread
creation took about 1.8 s in this run.  A persistent app-server amortizes that
cost, but the controller adapter should also suppress capabilities it does not
need and measure the result.  This startup observation is not model latency.

Integration requirements are now concrete:

- keep one app-server alive across planner turns;
- start a turn synchronously so the controller owns its thread/turn IDs;
- monitor exact observations while another thread waits for completion;
- on invalidation, send one interrupt and require interrupted completion;
- record missing partial usage separately from numeric zero;
- never parse or admit an interrupted turn's partial items;
- begin the next decision from a fresh observation with no inherited cover.

The next adapter should first pass a fake-protocol completion/interruption race
suite and a command-free capability-suppression probe.  Only then should it
replace the v25 one-shot planner bridge in a newly versioned controller.
