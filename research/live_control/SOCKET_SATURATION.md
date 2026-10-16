# Reserve cancellation admission separately from observation waits

Eight concurrent two-second observation waits fill event_socket_v3's handler
capacity. Each forwards a clock before waiting; nine runtime clock records
(initial plus eight blockers) establish that all handlers were active before the
probe sends cancellation. The regular endpoint returns busy/command_forwarded=false.

Candidate event_socket_v4 adds a second Unix socket in the same private directory,
with two independent handler slots. This endpoint accepts only cancel commands
and a read timeout no greater than one second. It forwards through the unchanged
CommandOnce registry and interactive_v23 admission. General requests still have
eight slots, and commands are not rewritten or given extended leases.

Both actual private-X11 xterm runs start a four-second Right-key hold. After the
busy response, v3 waits for the blockers to finish and retries; v4 immediately
uses the reserved cancel socket. These are intentional caller policies, not an
automatic fallback mechanism in the bridge.

| Metric | Shared capacity v3 | Reserved cancel endpoint v4 |
|---|---:|---:|
| Regular endpoint under eight active waits | busy, not forwarded | busy, not forwarded |
| First cancel attempt to verified key release | 1764.388 ms | 27.244 ms |
| Release before any long read returns | No | Yes |

The probe's raw cancel_request_roundtrip_ms measures only the successful request,
excluding the initial busy wait in v3; use the audit's first-attempt-to-release
metric for this comparison. The two metrics must not be substituted for each
other. Both terminate cancelled with verified release and recorded key admission.
Audit validates 24 exact AIT/PNG observations and listed source hashes. Retried
disconnected clock remains one command; total clock count is ten per run.

Evidence: `results/socket-saturation-v3`, `results/socket-saturation-v4`, and
`results/socket-saturation-audit.json`. `probe_socket_saturation.py v3|v4` runs
one fresh cohort; `audit_socket_saturation.py` audits both.

This is one scripted run per implementation, not a universal latency guarantee.
Two occupied cancel slots can still return busy. Both endpoints share a synchronous
stdin writer/registry lock: a blocked write can still prevent cancellation. No
priority or preemption exists inside that lock. Restart persistence, interrupted
parent cleanup and live negative tests of the cancel-only endpoint remain open.
Event boundaries are caller-selected and not yet filtered by action ID. The
reserved endpoint has ordinary local filesystem access scope, not new input
authority. No default promotion or freeze credit.

Next isolate the blocked-write failure boundary and make uncertainty visible;
do not infer successful cancellation from transport receipt alone. Preserve both
the busy baseline and verified owner release evidence when evaluating changes.
