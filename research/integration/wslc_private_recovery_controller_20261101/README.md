# Experimental private-display recovery controller

`PrivateDisplayRecovery` is an experimental one-shot coordinator for a
caller-owned disposable Xvfb and guarded owner. It validates that their display
name and explicit authority path match, calls cancellation, and on an unknown
result requests retirement of that exact display owner. It only reports that a
fresh display may be created when both the old guarded owner and the owned
display were reported retired. It never reports old-task success, old key-up
delivery, or replay permission from display retirement.

In one WSLc trial, an actual guarded owner sent `a` to a separate target, the
harness terminated that owner while `a` was down, and the controller called
real cancellation and retired the private Xvfb. No fixture release was issued
on the old display. A new private display and target then completed a guarded
`a` action with independent target effect and release, and ended neutral.
Old cleanup remained UNKNOWN and replay disallowed. The old target exited 1
when its display was retired; the fresh target exited 0.

Eight unit tests passed in normal and Python `-O` mode. They cover mismatched
display binding, owner/display retirement, failure and malformed receipts,
unknown status, duplicate token reuse and non-retirement cancellation. Earlier
red test output is preserved. The real trial, test outputs, source hashes,
pinned image and resource limits are preserved in the manifest and `raw.zip`.
The conditions' `draft_head` records the earlier common source ancestor;
the manifest identifies the actual candidate files. Authority files and
private commands are excluded, and both test cookie records were checked in
raw and hexadecimal form against the packaged material. The kernel reported
that the memory limit did not include swap enforcement.

The caller must maintain exclusive custody of both objects and every client
on the disposable display. Path equality is a consistency check, not a proof
of exclusive ownership or a secure server-generation identity. The coordinator
does not create or supervise the replacement application, enforce exclusive
access against other references, guarantee a hard end-to-end deadline, or
integrate into MCP. Killing the display may destroy application state and does
not establish queue drainage or old key-up delivery. This remains a draft
research primitive, not a production recovery guarantee.
