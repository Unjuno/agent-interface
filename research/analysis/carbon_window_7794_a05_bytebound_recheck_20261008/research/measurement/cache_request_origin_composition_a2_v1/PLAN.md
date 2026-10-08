# CACHE-REQUEST-ORIGIN-COMPOSITION-A2-20260918-002

H: REQUEST_ORIGIN_BOUND rejects a planner response whose runtime-owned request origin predates invalidation; INSTALL_TIME_ONLY launders at least one stale response by stamping install-time current epoch.

T: standard-library synthetic state machine, four scopes, planner generations {0,1,7,65535,2^31-1,2^63-1}. Exactly 150,000 independent microtraces / 600,000 transitions with the Issue #1360 category allocation. Candidate vs independently structured oracle after every transition. Construction uses disjoint literal IDs only. Source-first freeze/readback then formal1/reruns0.

D: exact #1360 gates: zero candidate/oracle result/state mismatch; 20k stale responses all refused; stale installs/effects0; fresh installs/effects>0; replay20k all refused/rebind0; HARD/AMBIG effects0; duplicate invalidation/cross-scope/generation/authority/malformed gates pass; INSTALL_TIME_ONLY stale effects>0; integrity/corruption pass.

C: refreshed semantic context must become a new runtime-owned request; planner generation remains provenance, not currentness.

U: synthetic semantics only; no model/GUI/X11/input/runtime promotion claim.
