# GPU supervisor transfer-inclusive break-even — allocation 10

Preparation package for Issue #5882. It preserves allocation-08’s zero-execution resource STOP and uses a fresh seed (49720261010), dataset, allocation identity and output namespace. It is not a rerun of a consumed allocation.

The exact CUDA image already appears in the local WSLc image inventory by repo digest. The protocol uses Microsoft WSL Containers (wslc.exe), which is the current coordinated route. Candidate, CUDA, auditor and retry counts are all zero. The formal run requires a coordinator-assigned, non-overlapping RTX 3080 window; an idle GPU snapshot or this preparation does not grant one.

See PREREGISTRATION.md, FREEZE.json and RUN_COMMANDS.md. H/T/D/C/U and limitations are explicit. No result is claimed until one candidate and its independent raw-only audit run.
