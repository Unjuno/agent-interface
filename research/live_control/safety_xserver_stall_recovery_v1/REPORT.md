# Issue #4167 — safety-plane release uncertainty across X-server stall/recovery

Decision: **PASS_XSERVER_STALL_RECOVERY_SCOPED** for allocation `safety-xserver-stall-recovery-4167-20260923-01`.

## Result

Six fresh formal cases ran once each after the public source-first freeze; reruns/replacements/tuning: 0.

- NO_WATCHDOG 3/3: F8 remained down at the +250 ms scientific measurement after the same Xvfb resumed. No KeyRelease appeared before measurement. Labelled parent fixture cleanup then released F8 and final state was neutral.
- PENDING_WATCHDOG 3/3: cleanup was requested while Xvfb was SIGSTOPped. `pre_resume_receipt=false` 3/3. After SIGCONT, the watchdog emitted exactly one KeyRelease and verified key-up 3/3; the application observed exactly one F8 press and one release; final state was neutral.
- Candidate SIGCONT -> verified key-up: 0.599754, 0.967354, 0.459062 ms; median 0.599754 ms, max 0.967354 ms. Frozen gates were median <=25 ms and max <=60 ms.
- Watchdog receipts retain `authority=cleanup_only`, `task_input_granted=false`, `input_dispatched=false`; no watchdog KeyPress exists.
- Independent raw-only audit: PASS, errors=[]; copied-evidence corruption controls rejected 10/10; all frozen source SHA-256 values re-match.

## Interpretation

For this private Xvfb/XTEST path, a release request made while the server is stopped must not be represented as confirmed merely because the safety process is alive or the request has been issued. The request blocks on the unavailable X server and becomes confirmable only after the same server resumes and key-up is independently observed. A cleanup-only watchdog can complete recovery after resume without acquiring ordinary task-input authority.

The baseline proves that pausing/resuming the X server does not itself neutralize the held XTEST F8 state in these cases. Parent cleanup after measurement is fixture hygiene, not candidate success.

## Construction / retained failures

Construction is excluded from the formal denominator. The retained sequence is documented in `CONSTRUCTION.md`: initial Xauthority/receiver setup STOP, stdout-framing STOP, parent scorer Xauthority STOP, then two complete construction revisions before the public freeze. No formal case preceded freeze commit `765445b61bd7df31bde20911c4d1b269d829141a`.

## Scope limits

Linux x86_64 provided execution container, CPython 3.13.5, python-xlib 0.15, Xvfb package 2:21.1.16-1.3+deb13u1. SIGSTOP/SIGCONT of the same owned Xvfb is one server-unavailability model. This is not evidence for server crash/restart into a new instance, physical HID/uinput, host crash or power loss, cross-platform behavior, a hard release deadline while the server remains unavailable, model/task benefit, or production readiness.

A component PASS here does not close #17, #2, #57, #59, or the global ROADMAP.
