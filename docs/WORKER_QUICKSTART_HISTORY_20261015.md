# Worker Quickstart

This page is the short operational route into the repository. It is navigation and coordination guidance; the linked goal, issue, evidence report, and acceptance gate remain authoritative.

## Before touching files or starting a run

1. Read [the current goal](CURRENT_GOAL.md) and the relevant [roadmap gates](../ROADMAP.md). Follow explicit current user direction when it changes the task priority.
2. Find the narrowest relevant open **and closed** Issue; follow its linked predecessors, latest comments, H/T/D/C/U, allocation, stopping rule, and retained outcome. An open Issue is not an allocation.
3. Check [open and closed PRs](https://github.com/Unjuno/agent-interface/pulls?q=is%3Apr), the selected Issue’s latest owner update, [maintenance/custody history #672](https://github.com/Unjuno/agent-interface/issues/672), and [resource ownership log #5085](https://github.com/Unjuno/agent-interface/issues/5085). Use [the retained research handoff](LOCAL_RESEARCH_HANDOFF.md) for context and follow [parallel coordination rules](ISSUE_FAILURE_CLASSIFICATION.md#parallel-coordination-and-evidence-preservation). Confirm that the proposed branch, output path, experiment, and resource window are not owned or in use; dated snapshots and older comments can be superseded by the owning Issue’s later correction.
4. Read only the relevant ledger section, report, raw evidence, and independent audit. Use the [evidence map](EVIDENCE_MAP.md) and [document authority map](README.md#document-authority-map) to resolve conflicting summaries.
5. Record a specific branch and additive path before work. Reuse neither a path nor a consumed allocation for a new result. Prefer WSLc (wslc.exe) for eligible local CPU/single-container experiments: use a pinned image digest, --pull never for cached-image runs, --network none where compatible, bounded CPU/memory, read-only source and a distinct writable output mount. Verify cleanup and record host resource warnings; do not assume --memory or swap limits are enforced until verified on that host. Keep Docker/OrbStack when a frozen contract requires Engine API, Compose, an unavailable isolation control, or GUI-specific behavior; WSLc work does not require starting the shared Docker daemon.

Preservation-time PR status: source PRs [#4375](https://github.com/Unjuno/agent-interface/pull/4375#issuecomment-5927755947), [#4406](https://github.com/Unjuno/agent-interface/pull/4406#issuecomment-5927757470), [#4410](https://github.com/Unjuno/agent-interface/pull/4410#issuecomment-5927759233), [#4438](https://github.com/Unjuno/agent-interface/pull/4438#issuecomment-5927760570), [#4440](https://github.com/Unjuno/agent-interface/pull/4440#issuecomment-5927761924), [#5119](https://github.com/Unjuno/agent-interface/pull/5119#issuecomment-5927763399), [#5163](https://github.com/Unjuno/agent-interface/pull/5163#issuecomment-5927764748) and [#5226](https://github.com/Unjuno/agent-interface/pull/5226#issuecomment-5927766062) were administratively closed without merging on 2026-10-01, 08:32–08:33 UTC. References to those PRs as open/Draft, including preservation-time “keep open/Draft” wording, are not current delivery-status instructions. This delivery-status-only interpretation also applies to preservation-time open/Draft wording for any other source PR whose later administrative closure is verified in its live history. Check the live PR history and latest owner-Issue instructions before acting. This clarification concerns only PR status: existing owner responsibilities and reservations, source-publication denials, missing source/raw/audit requirements, scientific FAIL/STOP/HOLD dispositions and no-rerun boundaries remain controlling. Closure does not authorize duplicate work, reopening, branch deletion, resource use, publication bypass or scientific promotion.

### Local Windows iteration runtime

On Windows hosts with WSL 3.x / WSLc available, use the Dockerless WSLc route described in [local container research](../.github/wslc-local-containers.md) for eligible new, disposable, single-container CPU tests. Check what the test launches as subprocesses before choosing an image: `python:3.12-slim` does not include `git`, so tests that create temporary Git repositories need a separately qualified image with Git. Keep network disabled when compatible, source mounts read-only, outputs on a separate writable path, image digests and source hashes recorded, and existing stopped containers untouched. WSLc `--memory` acceptance is not proof of an effective memory cap.

This local runtime choice does not change GitHub-hosted Actions or any frozen experiment protocol. Preserve Docker/OrbStack when Engine API, Compose, a required isolation control, GUI behavior, or a named runtime is part of the contract. Do not silently switch a consumed allocation to WSLc.

## During work

- Keep construction checks separate from formal results. Freeze source, image, inputs, commands, decision gates, and audit before a formal run.
- Preserve each attempt's first PASS, FAIL, HOLD, STOP, or infrastructure outcome with its identity, raw output, and hashes. Construction may be repaired and repeated with separate retained records; never retry a consumed formal allocation, overwrite or relabel its outcome, or pool old rows into a new result.
- A justified new formal allocation needs a separate identity, prospective freeze, and explicit deltas. A new allocation ID does not automatically require a successor Issue; reserve one for a genuinely new question or required integration decision. Follow the [allocation, construction, and successor boundaries](ISSUE_FAILURE_CLASSIFICATION.md#allocation-construction-and-successor-boundaries).
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
