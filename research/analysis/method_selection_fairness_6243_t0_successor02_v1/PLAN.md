# Issue #6243 T0 successor-02 — frozen plan and formal result

Status: METHOD_PASS_SCOPED_SYNTHETIC — one frozen Docker candidate and one independent raw-only audit completed; no retries. This validates the synthetic accounting implementation and decision gates only, not the substantive performance hypothesis.

Predecessor allocation method-selection-fairness-6243-t0-v1-20261002-01 is consumed and remains FAIL_AUDIT_GATE; its GitHub Issue comment and artifacts must not be changed or rerun. This package is an additive successor to correct the invalid equal-method-null fixture (18,000 vs 21,000 ms) and explicitly test the natural-method versus descriptive common-method views.

## H / T / D / C / U

- **H:** In matched synthetic task pairs where method-specific durations are identical across arms, a difference in natural method-selection frequencies can change whole-task ordering; a common-method descriptive view should show no within-method difference. A true equal-method null must stay exactly equal.
- **T:** 12 blinded trace pairs / 24 attempts. Four shortcut-mixture pairs have the same per-method times in both arms but different method frequencies and a one-time H acquisition cost. Four exact-null pairs use only the shared ordinary method and identical 18,000 ms duration. Two pairs include an H failed ordinary segment followed by a shortcut recovery segment; two include an unfinished H attempt with a fixed 120,000 ms penalty. Preserve every segment, failure, switch, timeout and cost.
- **D:** METHOD_PASS_SCOPED_SYNTHETIC only if two separately implemented deterministic annotators agree above the frozen threshold, a raw-only independent auditor reconstructs all 24 attempts and segment totals, the shortcut fixture shows equal method-conditioned means but the predeclared natural/acquisition horizon reversal (1 repeat H slower, 4/10 repeats H faster), the equal-method null is exactly equal, incomplete attempts and penalties remain, and four distinct mutations are rejected. This is an accounting experiment, not a human or system-performance test.
- **C:** Deterministic scripted annotations are not human coder reliability; acquisition charge and timeout penalty are constructed values. Natural-method totals remain the meaningful end-to-end endpoint; common-method comparisons are descriptive and selection-conditioned.
- **U:** No human tempo, agent GUI execution, causal method effect, population, product or external-validity claim. T1 needs eligible data or separate authorized participants and fresh GUI/model/resource gates.

## Execution gates

1. Before freeze: recheck current main, Issue #6243/PR/branch collisions, image digest/platform, and coordination Issue #5085. Host-only construction tests may run; they are not formal results.
2. Freeze sources and all gates as additive artifacts only after construction passes.
3. Request/grant one exclusive CPU OrbStack slot. Do not start a container without explicit slot release/grant and a fresh collision-free inventory.
4. Executed once in an isolated network-disabled OrbStack Docker container on 2026-10-02: candidate exit 0; independent auditor exit 0; retries 0. Auditor decision: METHOD_PASS_SCOPED, 24 attempts, four scenarios, no audit errors, 4/4 mutation controls rejected. Raw stdout, JSON outputs and source hashes are in formal-01/.
5. Run applicable local package CI; publish the raw bundle, hashes, and scope on #6243 and through a reviewable PR. Merge only after checks pass.

Image: python:3.12-alpine@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b, linux/arm64. Container used --network none, --cpus=1, --memory=512m, --pids-limit=64, read-only root, and 64 MiB tmpfs. Formal candidate/auditor invocations: 1/1; retries: 0. Exact command and environment receipt are retained in formal-01/EXECUTION.md.
