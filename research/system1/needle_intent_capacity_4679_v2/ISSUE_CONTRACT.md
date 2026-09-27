# Issue #4778 contract

This is a new-seed successor to #4679 and preserves #4679 / PR #4693 unchanged.
The only scientific comparison remains STATE_ONLY_24 vs INTENT_AWARE_24 vs
INTENT_AWARE_64 under the original synthetic teacher and 900-step recipe.
The new allocation primarily repairs the provenance gap with a truly pinned,
locally existing image ID, byte-identical GitHub source readback, and full
GitHub-retained raw outputs. No user data or external actions are involved.

Allocation: `needle-intent-capacity-4679-v2`  
Issue: https://github.com/Unjuno/agent-interface/issues/4778  
Branch: `research/needle-intent-capacity-4679-v2-20260927`  
Path: `research/system1/needle_intent_capacity_4679_v2/`  
Formal seeds: 4153201, 4153203, 4153207.

Decision vocabulary and thresholds are frozen in `PREREGISTRATION.md`.
Construction tests cannot call `fit` or consume optimizer steps. Formal may run
only once after the source and freeze are committed, fetched back and matched
byte-for-byte. Preserve all execution, raw, audit and infrastructure results;
no retries or silent relabeling.
