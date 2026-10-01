# Rank-1 online LoRA skill update — allocation v2

Issue #4507 retains the unchanged scientific question and gates. Allocation 01 remains a pre-training STOP; this v2 is a new formal identity with fresh seeds and a corrected output layout.

The fixed v1 trainer and independent auditor are read-only dependencies from the v1 STOP evidence commit. The v2 wrappers change only the allocation identifier, fresh seed tuple, and mount layout. Training writes to an empty `/out/training`; invocation metadata and audit output remain outside that directory. The rank-1 vs rank-2 intervention, model/data schedule, thresholds, image, resource limits, CPU mode, and no-retry rule are unchanged.

Exact v2 and dependency hashes are in `FREEZE.json`; `FREEZE.sha256` seals the manifest. Formal training begins only after the complete freeze is present on this branch and read back from GitHub.
