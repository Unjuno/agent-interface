# Win32 post-readback delayed-input counterexample

This finite diagnostic runs the `OperationOwner` implementation pinned from
current main `52df8e2d934bd8b20d4d36da8a7f17a524c49210` (source SHA-256
`f6ce2e9fa5bab634495b2a4361a45dd8a06ab480aa0dd445cd96ad2fee10938a`). It
drives the real Python custody gate through generation-A admission, producer
identity/retirement, recovery claim, accepted release, and an identity-matched
neutral readback. It then injects a delayed old DOWN into a separate fake
external-state variable and tries to admit generation B.

Observed result: generation A remains `recovered` with point-in-time
`release_confirmed=true`; generation B is admitted while the fake external
CTRL state is down. Both attempts retain `task_success=null` and replay stays
denied for the old operation. The experiment demonstrates that the owner has
no post-readback delayed-input quarantine. It does not show that real Windows
`SendInput` delivers an event late; no Win32 API, desktop, Docker, or WSLc was
used.

Reproduce from the repository root with `py -3.11
research/integration/win32_delayed_input_quarantine_20261028/reproduce.py`.
The script rejects source drift and writes only `result.json`. Run it under
normal Python and `-O`; the retained JSON should be byte-identical. This is a
counterexample to the current synthetic state contract and a requirement for
the next implementation slice: hold admission closed across an explicitly
declared late-event horizon, keep the old attempt unresolved during that
window, and only then admit a distinct generation after independent neutral
readback. The horizon still needs native Windows evidence before supporting a
physical-release claim.
