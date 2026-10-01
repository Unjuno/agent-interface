# Worker Quickstart

This page is the short operational route into the repository. It is navigation and coordination guidance; the linked goal, issue, evidence report, and acceptance gate remain authoritative.

## Before touching files or starting a run

1. Read [the current goal](CURRENT_GOAL.md) and the relevant [roadmap gates](../ROADMAP.md). Follow explicit current user direction when it changes the task priority.
2. Find the narrowest relevant open **and closed** Issue; follow its linked predecessors, latest comments, H/T/D/C/U, allocation, stopping rule, and retained outcome. An open Issue is not an allocation.
3. Check [open and closed PRs](https://github.com/Unjuno/agent-interface/pulls?q=is%3Apr), then [the current handoff](LOCAL_RESEARCH_HANDOFF.md) and [parallel coordination rules](ISSUE_FAILURE_CLASSIFICATION.md#parallel-coordination-and-evidence-preservation). Confirm that the proposed branch, output path, experiment, and resource window are not owned or in use.
4. Read only the relevant ledger section, report, raw evidence, and independent audit. Use the [evidence map](EVIDENCE_MAP.md) and [document authority map](README.md#document-authority-map) to resolve conflicting summaries.
5. Record a specific branch and additive path before work. Reuse neither a path nor a consumed allocation for a new result. Prefer an isolated container for repeatable experiments; check the exact lease and daemon before using shared compute.

## During work

- Keep construction checks separate from formal results. Freeze source, image, inputs, commands, decision gates, and audit before a formal run.
- Preserve the first PASS, FAIL, HOLD, STOP, or infrastructure outcome with raw output and hashes. Do not retry, relabel, or overwrite a consumed result; use a justified, distinct successor when the question changes.
- Keep work scoped to the Issue. Do not edit another worker's branch/path or interrupt a frozen allocation. Coordinate a genuine overlap with its recorded owner.

## Before handing work off

- Put outputs in a unique research path with a readable README/REPORT, exact reproduction steps, provenance and hashes, independent audit, result scope, and remaining uncertainty.
- Update the owning Issue with the observed result and decision. Open a focused PR to `main`; state whether it is evidence-only, construction-only, or runtime integration, and link the Issue and checks.
- Merge only when the PR is ready, checks and review gates pass, and any allocation gate is satisfied. A merged archive preserves evidence; it does not change the scientific status.
- Leave an explicit next owner/action or release the allocation. Do not delete a branch until its PR, unique commits, evidence paths, dependent branches and open work have been checked.

## Questions

- **What should I work on?** Current goal → roadmap → candidate Issue and its latest update.
- **Is this already being done?** Issue ownership/allocation → open and closed PRs → handoff → branch tip and unique commits.
- **Where does the result belong?** [Research placement guide](../research/README.md#research-routing); preserve historical evidence paths.
- **Can I clean up this branch?** Verify whether its tip is in `main`, its PR state, whether any commits contain the only retained evidence, and whether an active Issue or successor depends on it. If any answer is unknown, retain it and record the unknown.
