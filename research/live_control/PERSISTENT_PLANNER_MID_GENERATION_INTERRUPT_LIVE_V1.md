# Frozen post-delta planner interruption

One preregistered Luna-low turn requested a deliberately long structured
answer.  The driver waited for the first matching `item/agentMessage/delta`
notification, which contained the first two JSON characters, then sent exactly
one typed interrupt for the same thread and turn IDs.

The interrupt request was sent 0.137 ms after the delta reached the client.  It
was acknowledged 3.035 ms after send, and matching interrupted completion
arrived after 3.181 ms.  The server reports a 3,374 ms turn duration.  No agent
message completed, and the persistent adapter marked the turn cancelled with
no eligible answer.

No token-usage notification arrived, even though reasoning completed and an
answer delta had begun.  This is partial usage unavailable, not zero.  The run
does not quantify saved tokens because there is no matched uninterrupted arm
and the server did not report partial accounting.

This closes the main cancellation-mechanics gap exposed by v24: a planner
future can now be stopped after generation has begun without force-killing the
process or admitting partial output.  The evidence is one long text turn, so
it does not yet prove repeated controller-loop races or GUI quality.  The next
implementation step is a new controller version that couples v25's earliest
exact-observation invalidation to this typed turn boundary, while keeping local
input release and stale-cover discard as separate verified obligations.
