# Construction failure retained

The first frozen construction run returned `passed=false` with only the
`dwell_intervals` gate failing. The generated ledger was otherwise stable:
1000 rows, unique IDs 1000, A/B counts 600/400, `p_A=3/5`, and the
completion-only comparator `2/3`.

The defect was a specification/implementation mismatch in the lower bound for
right-censored integer dwell. The implementation used `HORIZON=4` as the
minimum censored value, producing A=`10/3` and B=`5/2`; Issue #1911's frozen
criterion requires strict censoring (`dwell > 4`) and therefore the first
unobserved value `5`, yielding A=`11/3` and B=`3`.

This failure is retained and is not pooled with the passing rerun. The repair
changes only that lower-bound interpretation; the source seed, population,
ledger schema, maximum bounds, and audit gates remain unchanged.
