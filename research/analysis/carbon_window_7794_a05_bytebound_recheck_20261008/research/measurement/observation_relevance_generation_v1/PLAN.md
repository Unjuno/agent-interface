# #1583 O3 generation-bound relevance gating

H: exact changed-tile gating is safe only when the relevance receipt is bound to the runtime-owned current relevance generation. Historical/missing/forged relevance must fail open to full-current forwarding; a fresh receipt may again suppress exact changes outside the current relevant/critical sets.

T: standard-library 64-tile synthetic state machine, independent history oracle, STATIC_RELEVANCE discriminator. Frozen seed 158020260918001; 200,000 histories: current irrelevant30000, current relevant30000, stale shift hidden40000, fresh post-shift irrelevant30000, critical outside20000, missing20000, wrong scope15000, forged generation15000. One formal invocation, reruns/replacements/tuning0.

D: candidate/oracle mismatch0; relevant/stale/critical false suppression0; current/fresh-current irrelevant suppression30000 each; missing/scope/forged fallback exact; static stale comparator false-suppresses >0; integrity controls pass.

C: current relevance correctness is assumed; this does not solve relevance inference. Production may reuse a broader currentness epoch rather than a dedicated relevance generation.

U: synthetic O3 freshness semantics only; no real GUI, task, token, latency or runtime-promotion claim.
