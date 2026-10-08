# Allocation-global one-shot owner v1

Status: **PASS offline construction; motivated by live-03 duplicate execution.**

The retained `formal_allocation_launch_owner_v1.py` scopes ownership by `(workflow_path, head_sha)`. Live-03 exposed the missing dimension: the same versioned workflow path ran once on `main` and once on another branch with different SHAs. Both receipts reported `matching_run_count=1` and both entered the formal step. Therefore head-SHA-local ownership is insufficient for an allocation whose identity is the versioned workflow path.

This candidate makes the workflow path the allocation identity, requires the current and canonical owner branches to equal `main`, and rejects truncated API views, missing-current views and malformed matching runs. A later run is rejected even when its head SHA differs.

Container validation: Python 3.13.5, 12/12 unit tests PASS, `py_compile` PASS. No model, GUI, ViZDoom or OS input was used for this construction.

## Live-03 retained evidence

Run `34970434429` on `main` and run `34970546156` on `orchestrator/O4/G1-map01-measurement-live03-5486ea20` both completed the formal probe. Both measurement integration audits and strict terminal-score audits passed. Run 1 measured key `a` at 265.618–266.213 ms and `d` at 265.247–265.710 ms; run 2 measured `a` at 257.724–258.214 ms and `d` at 257.470–257.782 ms. All four direct intervals had censor width below 0.6 ms; invalid/unmatched releases were zero. These are engineering replication evidence only because the allocation protocol was violated.

**Disposition:** `map01-measurement-integration-live-03` = **FAIL_DUPLICATE_FORMAL_EXECUTION**. Neither run is selected as the unique formal outcome.

## H / T / D / C / U

**H:** workflow-path-global ownership plus required-main-branch gating prevents a later SHA or branch copy from entering the same one-shot formal allocation.

**T:** 12 deterministic cases covering different SHA, wrong branch, earlier wrong-branch poisoning, pagination truncation, missing current, malformed matching run, duplicate API rows and ordering.

**D:** PASS construction iff 12/12 pass and any second matching workflow-path run is denied regardless of SHA. Live-03 remains failed; this construction does not retroactively repair it.

**C:** GitHub API pagination or eventual visibility can still hide a run; those conditions fail closed. A future workflow must also restrict `on.push.branches` to `main` and serialize contenders with non-cancelling concurrency before this check.

**U:** No end-to-end race probability is claimed. The next valid live allocation must use a new workflow path/allocation ID and may not reuse live-03.
