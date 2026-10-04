# A04 result — scoped construction PASS

The candidate ran once on the frozen PR #7692 head plus the local A04 source
change. The callback began at 0 ns, made a command readable, and returned at
125 ns against a 100 ns tail deadline. The tail returned `CENSORED /
command_ready` with `deadline_overrun=true`; it left the command unread, emitted
one tail sample, and the resumed iterator returned the command without a second
scorer callback. The independent raw-only audit passed 14/14 checks, including
all frozen source hashes.

This fills a boundary not covered by A03: A03's callback completed after 25 ms
but before its 250 ms tail deadline. A04 tests readiness when the callback
itself crosses the tail deadline. The first red regression on the current PR
head failed as expected; after the minimal adapter change, the targeted test,
V1/V2 suites, and V18 composition tests passed.

The result is deterministic construction evidence only. Readiness, time, and
callback behavior were controlled by a test double; no real stdin, OS
scheduling, Doom engine, game effect, input device, model, recovery, or MAP01
progress was measured. It does not grant or consume the separately gated live
Issue #59 allocation.
