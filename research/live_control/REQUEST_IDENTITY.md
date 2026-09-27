# Join transport requests to runtime rejection records explicitly

Private socket v8 inserts transport_request_id into forwarded command objects.
Callers cannot prepopulate that reserved command field. The existing CommandOnce
registry still validates the request ID, detects payload conflicts and suppresses
repeated writes. Interactive_v25 / request_correlation_v2 copy the bounded identity
into command and rejected events alongside runtime_request_sequence and the
separate caller-declared action ID. No association is inferred from arrival order.

EventCursor v3 / socket --read-request-id allow command/rejected boundaries to
match that request identity. Other requests' records stay in the returned prefix.
Missing identity returns identity_unknown. Request scope cannot be combined with
action scope or applied to terminal/effect events, which do not carry this new
request identity. Existing action-scoped waits retain their conservative rejection
handling; this change does not silently assign rejected attempts to a running action.

## Concurrent live evidence

Two private-X11 xterm submit attempts use the same action ID, same valid observation
reference and separate transport IDs. Two client threads send them concurrently.
The expired-attempt receives runtime request sequence 2 and validity-expired
rejection; invalid-attempt receives sequence 3 and unsupported-operation rejection.
Each independent read ends at its own rejection. Command/rejection joins agree
on explicit transport ID and runtime receive sequence.

Repeating expired-attempt returns the same rejection with replayed=true and no
new runtime command. Reusing that request ID with different contents produces a
transport conflict. Supplying a reserved identity field is rejected before the
runtime receives the command. A later valid program saves exactly t991024 and
independent evaluation succeeds. Source hashes, exact frames and owner close are
audited. Results: results/request-identity-01 and request-identity-audit.json.

These are two concurrently dispatched known negative requests in one live run,
not exhaustive scheduling/interleaving tests or proof of faster planner decisions.
The direct runtime can receive caller-supplied identity metadata; the label is not
authentication. Scope is one trusted local bridge/runtime lifetime. There is no
session incarnation, cross-restart uniqueness, durable exactly-once guarantee,
or full terminal/effect causal lineage. No default promotion or freeze credit.

Next use this explicit request/receive mapping to distinguish admitted-attempt
outcomes from later action completion without assuming that reused action labels
identify an attempt. Retain unknown identity for malformed input and unmodified
backends. Broader speed/token claims still require matched actual-assistant tasks.
