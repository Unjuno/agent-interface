# Eventfd notification failure under gated send: r544

One isolated Linux Fake X/MCP run used a normal positive control, a successful
notification with a gated send, and an injected notification `OSError` with
the same gate. The first two tests passed. In the third, the parent UNKNOWN flag
and reported notification failure were observed before the gate opened, but
the fake target subsequently produced its synthetic effect; the no-effect test
failed and the unittest exit was 1. Fixture gates enforce order; the retained
monotonic timestamps are consistent with it. The injected exception is not a
naturally occurring kernel failure or an actual cancellation.

The candidate stores parent UNKNOWN before calling the notifier and retains an
OSError type, with a separate mock test showing a later successful notifier call
does not erase the recorded failure. This only improves parent reporting. A
failed notification may leave the child uninformed; no fail-closed retirement
or X-server queue fence is established. Existing post-child-check races,
descriptor lifetime, notification hangs and other exception types remain
unresolved. No actual X input, physical release, task success or MAP01 was
tested. The prototype is not safe to merge.
The snapshot's notification fields are not read atomically and may temporarily
show an earlier or pending state during concurrent updates. Fixture teardown
attempts to retire the child, but failures before its nested close block can
still leave cleanup unconfirmed; fd closure was not independently checked.

`raw.zip` SHA-256
`d836fb8c1a46c9fbe575d38de963d85a8f5931e6bdbc3a33c9a34048f6965748`
contains the preregistered conditions, source diff and base, command output,
exit status and synthetic case files. Zip members were integrity checked.
Reports may reference original container temporary paths. The pinned image and
flags are recorded in conditions but not independently attested by case JSON.
