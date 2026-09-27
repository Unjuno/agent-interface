# Issue #3644 — formal-01 preregistration

Allocation ID: `issue3657-launcher-reap-order-formal-01`.

## Hypothesis

LibreOffice may create an `oosplash` launch process and a distinct
`soffice.bin` process that owns the visible Calc window. Binding lifecycle
evidence to the launch PID alone can miss the window owner. A dedicated
process group plus PID/start-time and XID reconciliation can terminate the
entire app fixture safely without touching a sentinel in a different group.

## Frozen one-shot procedure

1. In the pinned local image, create isolated HOME/XDG/LibreOffice state and
   private Xvfb `:143` with access control disabled only on that container-local
   display (no host display is mounted). Start Xvfb, then a Python sleep sentinel
   with a distinct session/process group, then LibreOffice Calc using
   `start_new_session=True`.
2. Within 30 seconds, select exactly one visible window whose title contains
   `LibreOffice Calc`. Record XID, title, WM_CLASS, `_NET_WM_PID`, and each
   relevant `/proc/<pid>/stat` identity (PID, start-time, PPID, PGID, SID,
   state) plus cmdline. Enumerate every process in the launch PGID immediately
   before termination. Launcher/owner PID inequality is allowed; membership
   requires same PGID and an unchanged PID+start-time identity.
3. Emit exactly one SIGTERM to the launch PGID, never to the container-wide
   process set. For at most 5 seconds, sample group members, every captured
   PID+start-time identity, and visible XIDs. Do not escalate, retry, or send
   normal GUI input. Record sentinel still alive before its own later cleanup.
4. Immediately after the one SIGTERM, call bounded `Popen.wait(timeout=1.0)`
   for the direct launcher child and record returncode/timeout. Then sample the
   remaining group. Later terminate the sentinel and Xvfb individually; record wait statuses and X socket
   disappearance. Preserve all logs and raw JSON.
5. Run a separate network-disabled container with source and raw evidence
   mounted read-only. Its independently written audit recomputes the
   classification and runs corruption challenges (forged owner group, retained
   owner after cleanup, killed sentinel, and raw-digest mutation).

## Outcomes

- `PASS_PRIVATE_PROCESS_GROUP_CLEANUP_SCOPED`: owner is bound to the isolated
  group; one group signal removes all captured group members and the Calc XID;
  unrelated sentinel remains alive; direct-child/Xvfb/socket cleanup and
  independent audit pass.
- `FAIL_PROCESS_GROUP_CLEANUP`: the observed owner survives the group signal,
  the Calc XID remains, or the unrelated sentinel is affected.
- `HOLD_PROCESS_OWNERSHIP_UNRESOLVED`: process ownership, start-time, group
  emptiness, or independent cleanup evidence is unavailable/contradictory.
- `STOP_PRIVATE_CALC_NOT_READY`: bounded Calc startup or unique owner discovery
  fails before the cleanup hypothesis is tested.

No retry or post-result adjustment. This is not a formal rerun of #3633.
