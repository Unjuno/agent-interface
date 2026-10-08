# Issue #3691 — audit artifact integrity successor

## H/T/D/C/U

- **H:** The merged #3676 auditor returns PASS for self-consistent replacement evidence and accepts JSON booleans where integer event counts are required.
- **T:** Preserve the #3675 raw/FREEZE; reject changed raw or freeze bytes using the hashes pinned by the study manifest; reject bool-as-int fields, duplicate JSON keys, and earlier transition mutations; compare direct API and CLI routes. Validate inside local Docker when the daemon is available.
- **D:** Native construction currently passes 6/6 tests. Docker validation is a separate required gate and is currently STOP because Docker Desktop's service/engine is unavailable.
- **C:** Offline audit only. No X11/input/model activity and no rerun of the predecessor formal allocation.
- **U:** Finite corruption controls do not prove complete auditor soundness or broaden any original XRes claim.

## Current status

The merged auditor and native Python counterexamples are recorded in `RESULT.md`. The new additive auditor enforces exact predecessor raw/freeze hashes from the study manifest, exact JSON types for counters and identities, and duplicate-key rejection. The original #3675 artifacts are copied byte-for-byte under `evidence/`.

No Docker Desktop PASS is claimed. After that local engine is available, run the tests in a network-disabled container with read-only source, then run the CLI in a second fresh container. Preserve this construction PASS and Docker STOP as separate outcomes.
