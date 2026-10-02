# Issue #6505 — independent audit-only successor A02

## H / T / D / C / U

- **H:** A fresh, independent raw-only auditor can reconstruct every one of the 11,111 retained #4889 rows and aggregate claims from the exact published bytes, and reject eight effective copied-evidence mutations without rerunning or changing the predecessor's `HOLD`.
- **T:** One audit-only OrbStack invocation rebuilds the retained ZIP from frozen base64 parts, verifies Git blob IDs and archive/raw hashes and lengths, independently enumerates reachable reducer states, pairwise commutativity, all event words through length four, and legal topological orders; it compares every raw row and summary, verifies the historical 7/8 no-op result, and checks eight effective controls. The output bind mount is provisioned empty; all config/inspect/host records are outside it. Original candidate/reducer/auditor runs=0; successor invocation=1; retries=0.
- **D:** `PASS_INDEPENDENT_AUDIT_SCOPED` requires exact source/archive identity, byte/CRC/row-count agreement, every row and summary matching independent reconstruction, historical negative-control agreement, eight effective mutations rejected, and no errors. Semantic/source mismatch is `FAIL_AUDIT`; inconsistent frozen evidence is `HOLD_SOURCE`; pre-completion infrastructure or setup failure is retained as `STOP` without retry.
- **C:** The predecessor's known defect is its mutation harness; a new implementation can still reproduce its finite result. Shared modeling assumptions remain possible.
- **U:** This audits only a finite authored reducer result. It says nothing about real event stores, GUI/runtime replay safety, concurrent effects, product guarantees, or latency/storage savings.

## Lineage and frozen inputs

Issue #6505; motivating #4889; construction precedent #4914; preservation PR #5393. Frozen latest-main base: `7446e22459ad79f57828b5699b95ef3c0b504917`. Original raw SHA256 `a25bc4a9e6cf845fb5b446b1d2d5071bd26909679efcc535372fdf77b58b4eb8` (3,241,590 bytes, 11,111 rows); archive SHA256 `a127e04d2fcce672f3ce5cc6f20d2af0e1f85b34ac16116e9e5a518e7c358f6b` (104,640 bytes). Exact Git blob identities are in `FREEZE.json`. The A01 STOP is preserved separately and is not repeated or repaired here.

## Runtime and budget

OrbStack Docker Engine, linux/arm64, cached `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, pull forbidden. Network none, rootfs and source read-only, separate empty writable output mount, 1 CPU, 512 MiB configured memory, 64 PIDs, all capabilities dropped, no-new-privileges, uid 1000. Configuration is not itself evidence of effective resource enforcement. Construction tests are separate from the single formal invocation.
