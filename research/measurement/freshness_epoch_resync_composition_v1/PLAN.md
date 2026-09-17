# FRESHNESS-EPOCH-RESYNC-COMPOSITION-20260918-001
BASE=ac6d784588f69ba8e99a3ad80408335a39838d1e
PARENT_1031_MERGE=ac6d784588f69ba8e99a3ad80408335a39838d1e
PARENT_677_RESULT_SHA256=41c4ee09751ecf7268b82abb6d0760d8433b5d84ccc47abc44e529ef057482e4
CAPACITY=4
MAX_AGE_NS=500000
PRIMARY_SEED=104020260918001
PRIMARY_SCENARIOS=50000

H: exact-overflow-bound resync advances epoch once, converts active gap to immutable historical gap, clears current epoch backlog, installs current snapshot, and preserves #1031 freshness/capacity semantics for future records.
T: hand-authored construction only before source freeze. After readback/ownership reread, one 50k positive primary corpus; candidate manager vs separately structured history-reconstruction oracle. Negative resync controls remain fixed construction/audit gates.
D: PASS iff 50k/50k candidate=oracle, historical gaps immutable, future coverage complete until new overflow, freshness/coalescing correct, cross-session isolation, stale/wrong/replay controls fail closed/idempotent, authority false.
C: resync may interact with freshness state and second overflow even though parent mechanisms separately pass.
U: deterministic in-memory semantics only; no transport, persistence, planner/model/task claim.
