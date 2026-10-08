# Issue #3657 — launcher reap order vs Calc group cleanup

Successor to #3644 formal-01 HOLD. This is a distinct, one-shot test of whether
the observed zombie was caused by delayed direct-child reaping in the observer.
It does not change or repeat #3633/#3644 evidence.

## H/T/D/C/U

- **H:** Reaping the direct LibreOffice launcher child immediately after the
  sole group SIGTERM will remove the observer-created zombie; any remaining
  members will then be actual non-reaped group members, independently visible
  from the window-owner identity and XID.
- **T:** One OrbStack Docker Linux/arm64 allocation, pinned image from the
  freeze, private Xvfb, unrelated sentinel in a separate session, Calc launcher
  in its own session. Record launcher and window-owner PID/start_ticks/PPID/
  PGID/SID, send one SIGTERM to that group, immediately `Popen.wait(timeout=1)`,
  then sample owner, XID, remaining PGID members and sentinel for at most five
  seconds. Preserve raw evidence; run independent read-only auditor and
  corruption tests. No retries or GUI/model/network operations.
- **D:** PASS only when direct launcher is reaped during the protocol, all
  captured members and owner identity disappear, XID vanishes, sentinel
  survives until explicit cleanup, Xvfb/socket cleanup passes, and auditor
  agrees. Owner/XID or sentinel counterexample is FAIL. Missing/ambiguous
  lineage or unreaped launcher is HOLD; Calc readiness failure is STOP.
- **C:** Same pinned image and isolated Calc startup procedure as #3644; the
  only planned difference is wait/reap timing after the single SIGTERM.
- **U:** Only this LibreOffice/Xvfb/Linux/arm64 observer ordering. No generic
  subreaper, host, native GUI, cross-platform or long-session claim.

Full allocation and output freeze is `FREEZE.json`; outcome goes in
`RESULT.md` and `evidence/formal-01/`.
