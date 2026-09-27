# #1099 excluded construction outcome

Status: **SETUP/INSTRUMENTATION FAILURE — no scientific disposition**.

The exact v10/v12/adapter source gates passed after one pre-construction plumbing-only Path-join correction. The granted excluded construction pair was then consumed exactly once: one V10 baseline session and one V12 candidate session.

Both fresh private-X11 sessions reached fixture readiness, but Python-Xlib failed before input with the same environment error:

`XauthError: ~/.Xauthority: [Errno 2] No such file or directory: '/opt/xvfb/.Xauthority'`

No F8 input was emitted, no application-effect row was observed, and no physical-edge scientific claim is made. Xvfb/Tk processes were cleaned up and X11 sockets were absent afterward.

Counts: construction sessions 2/2 consumed; formal invocations 0; reruns 0; scientific PASS/HOLD/FAIL = NONE.

Per the frozen #1099 stop rule, this setup failure is retained and #1099 is not rerun. A fresh harness-only successor may change only the private-X11 authorization plumbing (for example an explicit usable Xauthority path) before repeating construction; the scientific v10/v12/F8/150ms schedule and decision gates must remain unchanged.
