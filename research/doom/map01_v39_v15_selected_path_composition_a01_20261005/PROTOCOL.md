# A01 protocol

Issue #59 preregistration: comment 5986926684. The source tree is frozen at `f60752d0fb71595363a80977636ca74c1fd10b21`.

The one candidate extracts and executes the exact `session_command` function from V39 source lines 585–597 with `measurement_session=True`, then loads the returned current-main V15 path and calls its actual `main()`. V15 imports the current release-batch backend v1 and Executor v13. The V13 class body and V4/V3/V12/V10 owner source are loaded from frozen current-main snapshots. A test-double `session_map01_v12.main` observes the classes that V15 installs and drives one two-key sequence through release-batch backend v1. The typed backend parent, Xlib server, DoomGame and V12 main are inert stubs.

A read-only sampler is added at the owner-call boundary: only after `input_state` returns, then per-key telemetry is emitted. Capture every fake key event, XSync, query, owner receipt, route, and telemetry row.

Run the candidate once, retain stdout/stderr/exit. Run the raw-only auditor once. No retries or repairs after candidate execution.
