# Allocation 07 — withdrawn before execution

**Disposition: `STOP_WITHDRAWN_BEFORE_CANDIDATE`; candidate=0, auditor=0, retries=0.**

Issue #6308 records that the requested exclusive RTX 3080 timing interval was withdrawn after the user selected a different shared-memory feasibility question. This is an authorization/scope stop, not a scientific PASS or FAIL. The frozen package and fresh synthetic dataset are retained as historical preparation only; they do not constitute a GPU measurement.

The preregistered candidate required the exact PyTorch CUDA image, Docker Desktop runtime, fresh GPU/lease checks, and at most one candidate followed by one CPU auditor. No candidate or auditor was launched. Do not execute `RUN_COMMANDS.md`, replay this allocation, or present the dataset/source as a result. Any future transfer-inclusive comparison requires a separately authorized, newly frozen allocation.

This allocation is distinct from Issue #6329's shared-memory successor and its own source/runtime/lease gates. The latter does not inherit this allocation's authorization or data.

Source branch head before archival: `b89f3328d6974012eac9ab640bcf37a4c42a06fa`. All 12 files from that package are retained unchanged; `FREEZE.json` continues to record the original 0/0/0 invocation counts and source checksums.
