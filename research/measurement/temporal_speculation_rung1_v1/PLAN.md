# #1116 temporal-speculation Rung1

H/T/D/C/U are frozen in Issue #1116. This directory implements that exact container-only simulated-planner-gap allocation.

Fixed:
- seed 107420260918101
- universe {-2,-1,+1,+2}, K=2
- planner gap 100 ms logical; fallback verified effect at 101.5 ms + preparation compute
- branch-hit verified effect at 1 ms + preparation compute
- primary predictable80k + ambiguous20k
- controls reversal20k + expiry20k + no-authority20k
- one formal invocation; reruns/replacements/tuning0

Historical evidence ranks PREPARED/no-authority branches only. Fresh current realization + exact predicate match + fresh authority + non-expiry is required before admission.
