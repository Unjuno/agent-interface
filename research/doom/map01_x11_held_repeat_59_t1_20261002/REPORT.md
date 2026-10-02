# Issue #59 T1 — held-key autorepeat reaches a new focused client

## Result

`PASS_X11_HELD_REPEAT_REACHES_NEW_FOCUS` (one candidate, one independent
raw-only audit, zero retries). In the positive control, Xvfb's global repeat
was enabled and focused window A received 14 W `KeyPress` events during a
single 1.2-second held interval. In the distinct transfer condition, A received
the initiating W press, focus moved to B while the full 32-byte global keymap
still marked W down, and B received 14 W `KeyPress` events during the following
1.2-second interval before release. B's matching event sequence alternated
`KeyRelease`/`KeyPress` 14 times, consistent with the server's autorepeat
stream; no additional XTEST press was issued during that interval. Xvfb exited
0 and removed its socket and lock.

The narrow finding is that an app-event witness may become positive for a new
focused window later in the *same* held interval, even though the initiating
press went to the old focus. Thus the merged T0's zero B press in its immediate
50-ms observation window does not imply zero B key events over a longer hold.
It does not establish semantic app effect, nor contradict the immediate T0
result; it adds a later autorepeat phase.

## Frozen design and provenance

Allocation: `ISSUE59-X11-HELD-REPEAT-T1-20261002-01`.
H/T/D/C/U and STOP/FAIL/PASS gates: `PLAN.md`. Frozen identities and resource
limits: `FREEZE.json`. Source base: merged main
`ab43adce8141182f6bcfa76df469854b1ae11116`, which contains the T0 predecessor.
Image: `map01-attack-onset-phase-a2:20260927-r2`, pinned to
`sha256:fc3022d265f465748e0a39491e28f8447d0066266e00d2a8a9144e866bf148ed6`,
linux/amd64 emulated under OrbStack on arm64. Network disabled, 1 CPU, 768 MiB,
96 PIDs, read-only root, no-new-privileges, and a 96 MiB noexec/nosuid `/tmp`.
The existing shared `unjuno-native-ci-6092` container was not used or changed.

## Evidence and verification

`results/formal-01/raw.json` contains the full X11 event stream, timestamps,
actions, keymap samples, image/source identities, repeat controls and cleanup
facts. The raw-only auditor independently recomputed the result from that
record: zero errors, A positive-repeat count 14, B transfer-repeat count 14.
Five construction/mutation tests pass, covering scoped pass, bounded scientific
fail, malformed bitmap, focus-identity corruption, and missing positive repeat
(STOP). `SHA256SUMS` covers the frozen sources and formal outputs.

## Limits

This is private Xvfb plus synthetic XTEST protocol evidence. It says nothing
about a physical keyboard, actual OS input authorization, another X server or
desktop, real applications acting on these events, game input, threat response,
MAP01 progress/survival, latency generalization, safety, or efficacy. A delivered
repeat is not a useful-effect witness. This is one server configuration and one
key/run, not a frequency estimate.
