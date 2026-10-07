# A01 result

Disposition: PASS_METHOD_SCOPED_A01, not full Issue T0.

Candidate: 30 rows, eligible weight 3, proximal assignment effect 1.0, distal effect -2.0, executed-only contrast 4.0. Independent audit reproduced the 30-row table and oracle effects, confirmed all four NONIDENTIFIABLE controls, and rejected 10/10 mutations.

Raw candidate: `72bbe0063ad392d1bd7fd98f0d1bf41f97d302e1`
Raw audit: `61bd374c36066c48ac5df0678c87ec6239507a91`
Outcome: issue comment 5986033700.

A01 omitted a no-carryover comparator required by the originating Issue's T0. Do not upgrade it to full T0 or rerun it. A02 adds that comparator under a new freeze.
