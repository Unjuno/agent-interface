# Issue #39 recovery-stage provenance: preflight disposition

**Disposition: `STOP_NO_AUTHORIZED_MATCHED_PLANNER_ALLOCATION`**

**Date:** 2026-10-06

**Base:** `a3e6b0c1ab8d6af5c24abb88a451ce41c4ede028` (`origin/main`)
**Scope:** read-only eligibility/preflight; no scientific candidate, model call, GUI task, or container experiment was run.

## Question and preserved hypothesis

The 2026-10-06 refinement on [Issue #39](https://github.com/Unjuno/agent-interface/issues/39) asks whether trusted provenance for the failed recovery stage improves a planner's recovery choice when the final negative receipt is held constant. It distinguishes wrong intent, malformed schema, wrong mode, stale/wrong target, and accepted input with unknown external effect. Its hypothesis concerns the same-model planner's correct recovery choice, without more unsafe duplicates or false confidence.

This question is distinct from the prior deterministic typed-outcome contracts in #4967/#4174. Their finite contract results do not answer planner behavior. The #39 body specifies matched Calc/OpenTTD or desktop cases, same model/tasks/runtime/output limits, and a promotion gate spanning at least two domains. The refinement itself states that synthetic paired cases cannot establish live GUI benefit.

## Frozen next-run gate (not an allocation)

Before a planner-facing run, an owner must prospectively freeze a fresh allocation covering:

1. Two eligible task domains and an explicitly assigned model/runtime lane.
2. Matched case inputs, model/version/settings, prompt and output limits, retry budget, arm order, seeds, and the exact fixed final receipt.
3. Baseline arm: typed outcome only. Treatment arm: same outcome plus only independently supported stage provenance; otherwise `UNKNOWN`.
4. Held-out ambiguous cases and an independent oracle for intent, stage, external effect, duplicate/collateral actions, and recovery choice.
5. A bounded action vocabulary: repair schema, reobserve mode/target, reconcile effect before retry, reconsider intent/ask user, or abstain. Provenance grants no authority; unknown external effect never permits retry.
6. Exact cost comparability and decision thresholds for correct recovery, unsafe duplicates, false confidence, and abstention. Record model calls, tokens/usage completeness, round trips, and elapsed time.
7. Separate candidate and raw-only auditor programs/processes; one formal run per arm, zero retries, immutable raw and SHA-256 manifest.

Decision: scoped PASS only if held-out cases with independently available provenance improve correct recovery at comparable measured cost, with zero increase in unsafe duplicate actions or false confidence. FAIL on wrong-stage repair or blind retry. HOLD if provenance leaks fixture-only truth, is unavailable/ambiguous, or the comparison only relabels schema/mode controls. A synthetic/deterministic proxy is not eligible to satisfy this planner-facing gate.

## Preflight observations

- Current Issue #39 is open and its latest comment is the unverified stage-provenance refinement.
- The latest Issue #39 comment confirms #4967 tests only the pre-model negative-outcome contract and explicitly says planner-facing discrimination remains untested.
- Issue #4174 remains open with canonical disposition `HOLD_EVIDENCE_INCOMPLETE_AFTER_CONTAINER_RESET`; it prohibits rerunning its consumed 144-row allocation. That missing-evidence issue is separate from this new question.
- Live #5085 coordination says an idle host/runtime does not establish a resource lease and unassigned work remains deferred. No #39 planner/model allocation or assignment was found in the inspected records.
- OrbStack answers `orbstack` and `docker info` responds `29.4.0 OrbStack`; this proves only local engine availability, not allocation, model access, or desktop-task authority.
- Current `origin/main` was fetched and is `a3e6b0c1ab8d6af5c24abb88a451ce41c4ede028`. Existing PR #8228 remains separate; no #39 recovery-stage PR/allocation was found in the inspected records.

## Resumption condition

Resume only after the Issue owner/coordinator records a specific fresh matched planner allocation and eligible two-domain execution lane. Then freeze the exact sources, model/runtime, tasks, and decision gates before any model call. Do not reuse #4967/#4174 allocations or claim the present STOP as a scientific PASS/FAIL about stage provenance.
