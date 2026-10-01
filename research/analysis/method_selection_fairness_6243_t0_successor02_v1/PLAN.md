# Issue #6243 T0 successor-02 — preparation record

Status: FROZEN_NOT_LAUNCHED — no formal candidate/auditor run.

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
4. In the granted isolated network-disabled container, invoke candidate once; only if exit 0, invoke independent raw-only auditor once. Retries are zero. Preserve any FAIL/STOP verbatim.
5. Run applicable local CI; publish the raw bundle, hashes, and scope on #6243 and through a reviewable PR. Merge only after checks pass.

Proposed image (cached, read-only inspected): python:3.12-alpine@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b, linux/arm64. Formal invocation remains 0/0 until grant.
