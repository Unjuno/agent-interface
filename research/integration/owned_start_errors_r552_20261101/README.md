# Owned startup error checks r552

Eight direct owned-session tests passed in a normal Python run and in a separate
`-O` run in isolated Linux containers. The tests include a Fake X child spawned
before an injected startup exception, a child already exited at that exception,
an injected retirement exception, a pipe-close exception, and explicit UNKNOWN
reporting. The tests retain the spawned process reference and perform their own
fixture cleanup. A no-PID startup failure remains unconfirmed; close returns
unverified UNKNOWN rather than claiming no child exists.

These are scoped injected failures, not evidence that an OS start failure never
leaks a child. PID identity mismatch, partial Popen with no PID, BaseException
in cleanup, allocation failures before the existing try block, a live child
after failed retirement, supervisor custody and real X requests remain open.
The independent MCP shutdown/startup regression remains failing; these eight
tests do not prove finite recovery, input release or task success.
Review notes that the unregistered-reference close branch returns before
closing any existing supervisor or other registered owner, and has no
resolution/retry protocol. It can leave known resources alive and can keep a
truly unspawned case UNKNOWN indefinitely. Pipe-close failure types are retained,
but the affected pipe handles are not retained for a later cleanup attempt.

`raw.zip` SHA-256
`074b089222575238595747b5cecbe91d1385e989e7bec3785cfb236c68043c6b`
contains conditions, base, pre-run diff, source status and outputs/exit codes.
ZIP integrity was checked. The image digest and Docker flags are recorded
conditions, not independently attested by the unittest output.
