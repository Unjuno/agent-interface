# Construction run 01 — H/T/D/C/U

- **H:** Corrected role-separated adapter runner hashes the exact eleven declared data/label/schedule fields, including the A-base optimizer row schedule `base_row_indices`.
- **T:** Source was frozen at FREEZE SHA-256 `991f021b7f0e85785f847eaa16d692e487a1ebc62c0119dff236ee87d44cf581` and read back byte-identically from the GitHub branch. Cached CPU image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, linux/amd64. Frozen zero-update suite: 7/7 passed. Excluded construction seed 736514 was invoked once; formal seeds 736711/736811/736911 were not used.
- **D:** `STOP_CONSTRUCTION_OUTPUT_NOT_EMPTY`, container exit 1. Host stdout/stderr and invocation receipt had been placed in the same mounted `/out` directory before start. The frozen constructor stopped before `run_seed`; raw file absent, optimizer steps 0, formal fit count 0. STOP evidence auditor: `PASS_STOP_EVIDENCE_AUDIT`, errors `[]`.
- **C:** The guard behaved correctly. This is an orchestration/launcher mistake, not a quality result about role-separated skills. The exact STOP, invocation receipt and output logs are retained. No retry was made.
- **U:** Full-pipeline construction and its scientific raw audit remain unverified; all three formal seeds remain unspent. This allocation is consumed under the recorded no-retry construction protocol. The source-contract unit tests do not prove training behavior or GPU benefit.

The pinned image is CPU-only and the registered study explicitly fixes CPU execution. No GPU was used; moving this tiny synthetic study to CUDA would alter the treatment execution condition. The shared RTX 3080 also has other active GPU allocations.

