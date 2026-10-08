# #1792 mediated typed dependency ledger

## H
One AF_UNIX mediator can automatically emit exact typed READ, RESOLVE and QUERY dependency receipts for the three retained primitive families, while task configuration contains no authoritative state.

## T
One owner process holds all state and versions; one separately exec'd task process receives only socket path plus case id/kind schedule. Formal covers branch16, alias16, query32, malformed1. Owner retains per-case ledger. Independent auditor regenerates the typed ground truth from retained case state and checks post-prepare single-resource validation. One source-frozen formal invocation.

## D
PASS iff all 64 scientific ledgers exactly equal ground truth; unsafe acceptance=0; false invalidation=0; malformed op creates no receipt; task schedule fields are only id/kind; source/audit/invocation integrity pass.

## C
Protocol mediation is not arbitrary-code sandbox proof; #523 separately supplies Linux raw-store capability evidence.

## U
Scoped integration mechanics only; no production ABI, GUI/model/token/cross-platform claim.
