# #4295 specialist regeneration vs versioned lifecycle

Allocation: specialist-regeneration-4295-20260923-01

H/T/D/C/U are the Issue #4295 contract. Formal denominator is 8 schedules x 2 repetitions x 8 requests = 128 request rows. Each request row retains outputs for ALWAYS_GENERAL, VERSIONED_SHADOW_SWITCH, and REGENERATE_AND_ATTEST.

Formal decision gates:
- both candidate policies match independent predicate/graph oracle on all 128 request rows;
- stale/incompatible specialist use = 0;
- UNKNOWN coercion = 0;
- incomplete/corrupt/novel controls fail closed through GENERAL/YIELD before incompatible specialist consumption;
- on SUPPORT_VERSION_CHANGE + PRODUCER_GENERATION_CHANGE + RECOVER_COMPLETE_NEW_VERSION (48 request rows), REGENERATE_AND_ATTEST must use at least 8 fewer runtime GENERAL calls than VERSIONED_SHADOW_SWITCH;
- full-support attestation before every regeneration activation;
- authority_granted=false everywhere;
- independent audit errors=[] and >=10/12 coherent copied-evidence corruptions rejected.

Construction is disjoint and excluded. Formal is one invocation only; no rerun/replacement/tuning.
