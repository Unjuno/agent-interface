# R34 — Public task after orphan recovery (one frozen attempt)

## Question

Can the current-main public supervised Win32 MCP path recover an expired,
release-unconfirmed A dispatch while preserving that source as `UNKNOWN`, then
complete and independently certify a *different* task using a newly observed
target generation?

## Frozen protocol

One fresh native fixture; one public A dispatch with a 2 s authority lease; the
fixture schedules factual `a` at 6 s; at most one public orphan recovery after
exact producer-absence proof; one new foreground confirmation and fresh
observation; one distinct B dispatch; one task verification. No retries, no
model/provider, and no allocation beyond this single host-local trial. Conditions,
IDs, source code, and hashes are in `conditions.json` and `SHA256SUMS.txt`.

The independent oracle returns success only if the fixture state is exactly
`ab`, exactly one WM_CHAR B event exists within the B dispatch's recorded
monotonic interval, and the returned receipt is bound by the public server to
the B call ID, operation ID, and target generation. The first A effect remains
factual fixture evidence only. The oracle does not certify the UNKNOWN A action.

## Stop rules

Any pre-dispatch foreground mismatch, non-UNKNOWN/released source action,
producer identity uncertainty, invalid recovery receipt, non-neutral readback,
missed 2 s recovery horizon, non-clear durable fence, missing old `a`, follow-up
foreground/observation mismatch, B release failure, or oracle mismatch stops
this one attempt. Preserve all partial records and the fixture/fence if custody
is unresolved. Do not rerun the allocation.

## Limits

This is a controlled Win32 fixture, one attempt, one host, no provider/model,
and no MAP01/Calc/preview/economics claim. The task effect is tied to the exact
B operation through the single B event's time interval and the public
server-bound oracle receipt; it is not arbitrary-application or population
reliability evidence. A pass would establish a scoped recovery-continuation
case, not retroactively score A or prove general reliability.
