# Early stopped notification over the private socket

The existing executor v8 already emits input_stopped before optional passive capture, but event_scope rejected that event in action-scoped read boundaries. stopped_scope_v1 adds only its explicit id mapping. stopped_cursor_v1 and stopped_socket_v1 are explicit copies of cursor v5/socket v11 using that mapping. No global/default scope or existing measured transport is edited. Request-scoped boundaries are unchanged; this candidate uses action_id scoping.

## Actual transport experiment

results/stopped-transport-01 pins the new sources. stopped_transport_fixture_v1 uses executor v8 with a synthetic focus interruption and a capture gate in a child process. The actual AF_UNIX server, bounded command writer, once-only forwarding, event cursor and separate cancellation socket carry the requests. The fixture is not X11 and does not model real pipe saturation.

Seven socket exchanges verify:

1. Clock and explicit submit with a five-second deadline.
2. Submit waits for either own input_stopped or own terminal. It returns input_stopped before the capture gate is released, with the original focus_changed reason. Measured submit round trip was 35.498249ms in this synthetic case.
3. A terminal-only read times out while capture is confirmed entered and blocked; the process remains live. No restart follows that timeout.
4. A new submit is rejected as closed or busy; no premature admission or tail execution occurs.
5. The cancellation socket returns matched=true while capture is still blocked.
6. Explicit gate release lets the already-started snapshot return; executor v8 skips remaining captures and returns needs_decision with stopped=true and one completed passive capture.
7. Finish exits the bridge and runtime with code zero. All 13 recorded runtime events are matched to contiguous socket reply slices, including the final stream-close read.

The probe also checks baseline action-scoped input_stopped rejection, matching support in the candidate, foreign-action non-boundary behavior and missing identity uncertainty. Early events do not consume stream history or grant input permission.

## Interpretation and next integration

This demonstrates that a new asynchronous capture worker is not required merely to deliver an early interruption on the existing separate socket. input_stopped means verified input release with passive work still pending; terminal means that worker has finished its program/observation lifecycle. The tested pending state is inferred from the early event and unresolved terminal, and confirmed by busy rejection. A production client should represent those states explicitly rather than optimistically submit again.

Remaining work: integrate this boundary into a live client that returns the early reason, keeps a pending capture cursor, handles terminal arriving in the same/bounded batches, and can request stop without retrying input. Compare when to surface early versus wait for useful followup images on actual Calc transitions. A genuinely blocked output path can still delay input_stopped publication, and a blocked synchronous capture still delays terminal/close. No preemption, actual-X11 latency, model receipt time, human-speed or token-cost claim follows from this fixture. Defaults remain unchanged.
