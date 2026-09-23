# Issue #2985 semantic FIFO2 ordering — independent producer result

Task: `FIFO2-SEMANTIC-ORDER-2985-20260920-01`  
Image: `python:3.13-slim`  
Network: `none`  
Runner SHA-256: `77b8f60b84d114f8c6f22593b77fc4b0cd2d72628304283a3a91f7964ceaf40a`

## H / T / D / C / U

- H: independent producer transaction serialization does not guarantee semantic event order; a sequence-aware owner must hold E5 until E4 exists, while a commit-order FIFO can expose E5 first.
- T: two independent producer processes/connections, each using `BEGIN IMMEDIATE` and one committed offer, compared under candidate and unchanged commit-order control. Include reverse/forward arrival, same-sequence duplicate, unknown sequence, noncritical interleave, ACK replay, and restart/resend.
- D: `PASS_SEMANTIC_FIFO2_ORDER_SCOPED` requires no early E5 delivery, exactly-once behavior, safe ACK replay/restart, malformed rejection, and independent audit.
- C: one local SQLite topology, bounded 10-row schedule, one container image; no distributed ordering, network durability, crash atomicity, throughput, or production queue claim.
- U: candidate is additive and separate from #731's retained positional FIFO; timing is descriptive, not a race-rate estimate.

## Result

`PASS_SEMANTIC_FIFO2_ORDER_SCOPED`.

The runner produced 10 rows (five cases × candidate/control). Independent audit errors: zero.

- Reverse E5-before-E4: candidate delivered E4 then E5; control delivered E5 then returned `EVENT_NON_MONOTONIC` for E4.
- Forward E4-before-E5: both delivered E4 then E5.
- Same sequence: competing E4 identity was `DUPLICATE_REJECTED`.
- Unknown sequence: E9 was `UNKNOWN_SEQUENCE`.
- Noncritical interleave: candidate retained semantic critical ordering while accepting N6 after the critical predecessor path.
- ACK: every row returned `ACK_APPLIED` then exact replay `ACK_ALREADY_APPLIED`.
- Restart/resend: already committed events returned `DUPLICATE_REJECTED`; no duplicate delivery occurred.

The reverse-arrival discriminator demonstrates that storage mutual exclusion and semantic sequence ordering are separate boundaries. The result is scoped to this candidate/control, SQLite topology, and schedule.

