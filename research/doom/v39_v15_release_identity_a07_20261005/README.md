# V39/V15 release identity A07

This package retains an audit-only successor over the immutable A02 synthetic fake-X raw. It tests whether every release transition binds to exactly one preceding admission by `(id, intent_token, owner_id, step, key)`.

The TDD construction phase reproduced that the retained A06 auditor accepts an admission `id` mismatch, then the A07 implementation and independent reference tests accepted the untouched baseline and rejected 14 single/composite identity mutations plus a duplicate release. These are construction results.

The formal A07 auditor emitted a baseline pass, but the saved exit record conflicts with the terminal output. The frozen independent reference command produced no audit file. Per the preregistered gate, the allocation is **STOP**, not PASS. No retry or post-freeze source edit occurred. The original A02 `FAIL` and A03/A06 records remain unchanged.

See [PROTOCOL.md](PROTOCOL.md), [FREEZE.json](FREEZE.json), [RUN_RECORD.md](RUN_RECORD.md), [STOP.json](STOP.json), and [formal outputs](formal/). This fake-X audit establishes no real X11 or physical key state, application effect, useful feedback, latency, recovery, live threat response, gameplay, or safety result.
