# Formal allocation 01: container launch STOP

Task `ISSUE3311-LOCAL-X11-INTERMEDIATE-FEEDBACK-20260928-01`; parent Issue
#3311. Frozen against main `6906d6d9b5679604a5d997c89edd1b1789f849ed`.

**Disposition: `STOP_CONTAINER_ENTRYPOINT_PREEMPTED_RUNNER`.** The pinned local
ARM64 image starts a historical default Python entrypoint for a different task.
The requested runner was therefore treated as argv to that entrypoint, which
exited 2 before importing the frozen test code. The Xvfb server, Chromium page,
GUI action, model/provider call, and runner result were all absent (zero).

This is an execution-setup failure, not evidence for or against the hypothesis.
Per the freeze, allocation 01 is not retried. The exact command/output and
frozen runner/auditor digests are retained in `CONTAINER_LAUNCH_STOP.json` and
the preceding Issue #3311 comments. The known correction is to override the
image's entrypoint explicitly; any attempt must use a new allocation ID and a
new preregistered invocation, preserving this STOP unchanged.
