# #1501 Batched matched-source temporal query preflight

TASK: `TEMPORAL-QUERY-MATCHED-SOURCE-COVERAGE-BATCHED-20260918-002`
PREDECESSOR: #1498 no-result execution stop
BRANCH: `research/temporal-query-matched-source-batched-1499`

Only changed factor: execution envelope. Scientific design and decision threshold are unchanged from #1498.

Formal universe: master seed 149820260918002, indices [0,220000), 20 immutable batches, 11000 histories/batch. Each case RNG is independently derived from SHA-256(master_seed:index), so batch boundaries do not affect cases. Aggregate sums integer counts before computing rates.

PASS: complete exact index coverage; mismatches/leakage 0; query not worse in any class; overall advantage >=15 pp; independent audit PASS. No batch replacement/rerun.
