# A06 Adapter Follow-up — 2026-10-12

This follow-up tests `research/live_control/input_owner_process_v1.py`, a stricter framed socketpair adapter with lease/focus/surface transport and an fsynced recovery receipt. It is separate from the preserved A06 candidate and does not alter A01/A02 evidence.

## Result

Protocol unit tests cover lease identity, cancellation state propagation, exact fields, request sequencing, key allowlisting, observed focus, and recovery receipt cardinality. They pass under the available Windows Python standard library.

The adapter's normal-close case passed once under WSL2/Xvfb: one verified `owner_release`, empty keys/buttons/unknown/error fields, stopped V12 thread, and fsynced receipt. Its SIGKILL experiments did not produce a verified release receipt. In one setup the Xvfb server was terminated with its launching shell; in later attempts the service's Xlib connection reset when the session parent was killed, even when the Xvfb process remained visible. Those runs are STOP and are not evidence of recovery.

The A06 runner remains the valid lower-bound evidence: it uses a single Unix stream socket, keeps Xvfb and the subreaper in one supervisor, collects the detached owner process, and passed A02 with the real V4/V3/V10/V12 stack. The new adapter has not been integrated into `doom_owner_thread_release_batch_backend_v1.Backend`, `session_map01_v15.py`, or the outer V39 controller. In this worktree, the V39 controller's frozen source snapshot references a V15 session launcher that is not present in the snapshot, so a safe controller composition test cannot be completed here.

## Follow-up needed

Before integration, rerun the framed adapter under the A06 subreaper harness without changing the display supervisor lifetime, add the ordinary explicit-up and multi-key cases, verify asynchronous interruption delivery to the caller lease, and make the outer controller require the service receipt before display reuse. Until then, the adapter is experimental and must not be selected by a session or live-control path.
