# UNPOSTED evidence-delivery record

Retrospective registration candidate, not public preregistration:
"Fixed-byte historical snapshot index memory depends on record density (c5d2)".
Related #3985, b7e1 and #4068 (non-overlap). Keep publication incidents in this
question; do not create a wrapper-only Issue. Preserve every old result.

One locally source-frozen nine-case allocation at constant1MiB,128/1024/8192
records x3 repetitions, max_records32; exact b7e1 eager implementation unchanged.
PASS_INDEX_DENSITY_MEMORY_SCOPED. Retained Python allocation medians29721/259521/
2130297 bytes; ratio71.67649; entries129/1025/8193. Input existed before tracing;
not RSS, whole memory, tracer storage, query memory or an unbounded-memory claim.
All9 workers and outer process exited0. Full110271 traces/28041 prefix entries;
raw-only audit errors0;10 semantic corruptions rejected. No formal rerun.

Earlier proposed demand-index comparison STOP_PARALLEL_DUPLICATE_BEFORE_FORMAL
when #4068 appeared. Formal0;9 unit tests/3 smoke cases excluded and preserved.
Previous b7e1 archive387 files/386manifest entries revalidated, audit byte-exact,
11 tests pass, no old formal run. Do not count #4068 as this worker's experiment.

Only proposed new path research/integration/snapshot_index_density_c5d2_v1/;
local branch research/snapshot-index-density-c5d2-20260922. No remote Issue/PR/
branch/commit/comment was written. #4012 remains incomplete/Draft on latest read.
Original exact-source/raw publication through a reviewable PR is still required.
