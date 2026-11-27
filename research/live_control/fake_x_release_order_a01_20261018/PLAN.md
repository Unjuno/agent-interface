# Fake X release-order counterexample A01

Parent question: #17, whether cleanup can remain live when input transport is
blocked while preserving one serialized authority. New local construction ID:
`fake-x-release-order-a01-20261018`. No WSLc/container/live allocation is used.

## H / T / D / C / U

**H.** A second X connection can send an UP while the input connection is
blocked, but an empty readback on that second connection may be false evidence
if the original DOWN is still pending or blocked before send. Same-connection
cleanup should remain ordered but unable to return until the blocked call exits.

**T.** Use actual `X11Backend.key_state` to create the held-key obligation and a
deterministic Fake X server with per-connection queues. Compare a healthy
single-connection control, same-connection cleanup while `sync` is blocked,
release-connection cleanup while the DOWN is blocked before send, release while
the DOWN is queued before server processing, and a server-wide processing stop.
Record the event schedule, held ledger, server state, release receipt and
whether the original writer has returned. Run exactly once in normal and
optimized Python. The probe uses fixed barriers, with five seconds only as a
harness escape; no wall-clock threshold is evaluated.

**D.** `COUNTEREXAMPLE` if the independent lane returns verified-empty before
the original writer resumes and the late DOWN leaves the Fake X key held while
the ledger is empty. `SCOPED_ORDERING` only if same-connection cleanup stays
unreturned while its sync is blocked, then executes after the DOWN and returns
neutral; and a server-wide stop yields no release receipt until resumed. Any
other sequence is `HOLD` and retained. No outcome can establish physical X11
ordering or a release-time bound.

**C.** The modeled per-connection queue order may differ from a real X server's
scheduling. A real connection can block before send, after send, during reply,
or because the whole server is stalled. A separate connection may help one
interleaving and fail another; no result here qualifies the actual transport.

**U.** Synthetic Fake X schedule only. No real display, OS input, bridge/MCP,
MAP01, app effect, recovery, live timing or efficiency is measured. In
particular, an empty Fake X bitmap is not independent release confirmation.

## Decision fixed before collection

Do not promote a second connection from this evidence. A single false-clear
counterexample rejects “separate UP connection + its own empty readback” as a
bounded-release proof. The useful result is the exact pending-send ordering
that any future candidate must fence or keep `UNKNOWN` until the original
writer is retired and no later DOWN can arrive. Preserve all rows, including
any deviation from this prediction.
