# Report — current-main reconstruction of successor #2095

Decision: **PASS_ACTION_CONDITIONED_ROUTING_REPAIR_SCOPED**

- 8 finite cases; 5 malformed/unknown; mismatches=0.
- Valid save/move routes use disjoint declared region sets.
- Non-string, incomplete, unknown, and malformed intents fail closed.
- Raw evidence is returned by route output in all 8 cases and its SHA-256 is retained.
- Authority=true count is 0; model/GUI/network/runtime/task input count is 0.
- Independent audit PASS from an unrelated cwd in the predecessor reconstruction.
- Container execution unavailable; this remains a local standard-library result only.

This r2 is a source/path reconstruction from current main and does not reinterpret or modify #2059 or PR #2095.