# App-server response ownership

An unsolicited well-shaped response for future ID 2 could be cached while
request 1 was active, then consumed by request 2 before its own response.
Boolean true could alias a minted integer request ID,
and an id+method server request could be consumed as a reply. Retained C01
and C02 evidence remains separate from this ordinary source repair.

The client now reserves each minted ID under its existing condition before
writing, admits Python int/float JSON Number/no-method responses whose numeric ID is
currently reserved, and removes the reservation and leftover response in
finally on success, protocol error, timeout, EOF or write failure. Existing
integer IDs, error handling and one-send behavior remain. Concurrent active
requests can receive replies in a different order. Other packets remain in
the notification queue without being acknowledged or granted authority.

This changes the old accidental contract that a reply for an unissued ID
can satisfy a later request. The EOF fixture now emits its response after
request issue but before the caller begins waiting, then closes stdout.
The held-journal stderr fixture bypasses sent journaling with a directed
real pipe input and explicitly reserves that ID; it remains a test fixture.
The first two existing-fixture failures are retained, not relabeled.

The separate stderr source from Draft #7094 is byte-preserved outside the
three correlation methods. This candidate depends on that exact source;
it does not amend #7094 or inherit any votes. The new fixed content needs
its own review, and delivery to main must qualify the then-current whole
candidate, dependency delivery, platform requirements and sole sender.

Validation: baseline RED captures unissued response consumption. Ten new
ordinary constructor/queue tests cover Boolean/float IDs, request packets,
future success/error, immediate active response, genuine typed error,
timeout-late packet, write failure and concurrent reverse replies.
These plus nineteen stderr/EOF/journal/reader methods pass normal and -O.
The queues and static packets are environmental substitutes, not a model,
provider or live computer task. Existing OS-pipe regressions are ordinary
source-change checks; consumed C01/C02 producers are never replayed.

Limits: registration before write is an ownership reservation, not proof
that the peer received the request or that a packet is authentic. An
invented packet for an active ID, duplicated active replies, complete
response-shape validation, arbitrary malformed JSON, request approval
handling and bounded notification/quarantine storage are not resolved.
Request timeout still excludes time spent writing/journaling. Sensitive
diagnostics, physical release, actual task effect and resource savings
retain all #7094 limits. No live readiness or broad reliability claim.

I13 compatibility revision: current main accepts equal integral JSON Number echo (1.0 for issued1). Boolean remains excluded; pending ownership excludes unequal/fractional/unissued numbers and method-bearing packets. This changes earlier exact-int-only policy and its float-alias regression; original7237 source and first contradictory results are retained. Fresh content review required, no old-vote transfer. General JSON-RPC2 Number typing supports this local compatibility interpretation; this is not full Codex schema validation.
