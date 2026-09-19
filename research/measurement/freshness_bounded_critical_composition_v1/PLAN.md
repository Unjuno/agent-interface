# FRESHNESS-BOUNDED-CRITICAL-COMPOSITION-20260918-001
BASE=e690e155aa00fb72a30586513caf9bfeec9a8a7d
PARENT_FRESHNESS_BLOB=404a452aa304b4bde73ec0182450d241e2a744af
PARENT_OVERFLOW_ISSUE=665
CAPACITY_PER_SESSION=4
PRIMARY_SEED=103120260918001
PRIMARY_BATCHES=75000

H: Add only a per-session critical capacity of four with explicit RESYNC_REQUIRED overflow metadata; preserve #1021 freshness/coalescing/source-order semantics exactly.
T: construction uses fixed hand-authored cases only. After source-first freeze/readback and ownership reread, run exactly one 75k-batch deterministic primary corpus with candidate vs separately structured oracle, then independent audit/corruption checks.
D: PASS iff candidate=oracle on all batches, no silent critical loss, retained critical <=4/session and prefix/source order exact, stale noncritical delivery=0, fresh noncritical <=1/scope and newest, overflow gap identity/count exact/session-scoped, authority=false, malformed controls fail closed.
C: composition may reveal interactions between bounded critical retention and state coalescing not visible in either parent alone.
U: deterministic queue semantics only; critical classification completeness, planner response to RESYNC_REQUIRED, persistence/model/task benefit/live watcher behavior remain untested.
