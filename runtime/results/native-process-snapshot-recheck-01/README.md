# Process snapshot follow-up: no separate status call in this trial

The primary assistant used source 9eba35b7a in one fresh WSL Inkscape allocation,
seed 991123, two stages, through one persistent MCP relay. Both action requests
are byte-identical to the preceding `native-process-snapshot-live-01` trial.
The assistant viewed three returned images, consumed stage 2 / sequence 7 from
the continuation, saved the rectangle and used finish_after on the last action.

The last response included evaluation success, cleanup completed and a terminal
process snapshot with PID 19984 / returncode 0. The assistant therefore omitted
native_status and closed the relay on EOF (session 87828, exit 0). There were
three tool requests: start and two submits, versus four in the preceding trial.
No replay or corrective GUI input occurred. The ready action snapshot correctly
used initial_source_stage=1 alongside continuation.stage=2.

The final image and saved SVG show X=74, Y=50, width=40, height=30, no transform.
X=74 is the observed result; the public task is directional movement with
preserved geometry, not exact dx. Process exit does not supply evaluation or
cleanup evidence; these remain distinct fields from the final harness reply.

This is one observed omitted status call, not proof of a causal speedup or a
reliable one-call reduction. The internal first/second poll branch was not
instrumented, so different process timing may explain terminal availability.
Host presentation, model token/cost and human baseline remain unmeasured.
The previous negative result remains unchanged. No container execution occurred.

Run `python audit.py` to verify manifest hashes, all three exact image payloads,
matching prior requests, continuation linkage, releases, saved geometry and
terminal state carried in the final submit response. The manifest covers every
retained file except itself. This is same-assistant programmatic evidence audit,
not an independent review or a fresh execution of the application.
