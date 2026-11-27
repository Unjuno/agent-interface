# Blocked owner I/O with independent X11 release A10

**Status:** `PARTIAL / 1 TRIAL PASS / BATCH STOPPED` (2026-10-19).

A09 exposed a reply-gate race: the pump checked the gate before `recv`, then could forward bytes after closure. A10 serializes gate closure and downstream sends, rechecks under the gate lock after each receive, counts server reply bytes held, and requires a positive withheld-reply receipt before accepting the blocked-owner phase. A deterministic local socketpair test forces the relay to be blocked in `recv` before closing the gate; it verifies no early bytes escape and the held reply is forwarded after reopening. Result: `PASS_GATE_CLOSED_AFTER_RECV_AND_RELEASED_BYTES_VERIFIED`.

A10 also terminates/reaps the receiver before deleting its temporary directory. The Xvfb trial scope and owner/release checks are otherwise unchanged from A09. A01–A09 remain immutable records.

This remains Xvfb-only evidence for a responsive server with the owner reply path blocked. It does not establish permanent X-server nonresponse, physical desktop behavior, XWayland, or real application task completion.

## Preserved WSLc outcome

Trial 1 passed the scoped sequence: receiver KeyPress/key-down, XSync remained
blocked with 32 server-to-owner bytes held, owner kill/reap in 1.276 ms, exact
XRes client disappearance in 1.944 ms, independent KeyRelease receipt, key-up
readback, and key-up after 50 ms. The raw row is retained below the dependency
install output in `raw/wslc-run-raw.log`.

Trial 2 stopped before input because `client_is_connected` returned false for
the reported owner base. The source currently reuses a single
`owner-ready.json` between trials, so a stale trial-1 record may have supplied
the disconnected base before trial 2's process wrote its new record. That is
the leading source-based explanation, but the A10 raw does not log the value
read on trial 2 and therefore does not independently prove it. This is not a
release failure. A11 gives each owner readiness/command/sync marker a unique
trial path before seeking the remaining seven or eight clean repetitions.

`run-result.json` records exit 1, one completed trial, and the raw SHA-256. The
exact A10 container ID was queried after completion and was absent. The result
is `SCOPED_SINGLE_TRIAL_PASS / REPEATABILITY_PENDING`, not a batch pass.
