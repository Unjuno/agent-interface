# Consolidation status r27 — 2026-10-19

This is a dated restart point for the repository-wide plan, not a claim that all open work has been semantically classified.

## Current open-work inventory

At `2026-10-18 19:32 UTC`, GitHub CLI returned 1,675 open Issues and 515 open PRs for `Unjuno/agent-interface`. The comparison baseline was `origin/main` at `31c338fc8fecf3ef93ad802d2ac7ebee3bb9ff71`.

| Surface | Current count | IDs added since r15 | IDs removed since r15 | SHA-256 of full CSV |
|---|---:|---|---|---|
| Issues | 1,675 | none | none | `DE08A2A807960D68D22D8E4B95C10DC57D6209E8F9A90FD4B39EDD5358A72075` |
| Pull requests | 515 | #9064 | none | `A4CF43906092058D413F76FA99C554382CBC0493FAB0BC18A92FFE0F7F691BFF` |

Full metadata is in [open Issues r22](open-issues-20261019-r22.csv) and [open PRs r22](open-prs-20261019-r22.csv). The snapshot updates titles, timestamps, labels, assignees, and PR head/base metadata; it does not decide meaning, current ownership, mergeability, completion, or safe deletion. The prior r15 CSVs remain unchanged for the exact membership comparison.

## What “clean” means

- Every reviewed research idea has a source Issue, distinct hypothesis, linked results and limits, unresolved dependency, and a finite next test or evidence-based rejection.
- `untriaged` and `unverified` remain visible states. Do not infer completion from a summary, a closed Issue, a merged evidence-only PR, age, a similar title, or lack of an assignee.
- PR disposition and Issue disposition are separate. A verified PR may be integrated while the parent research Issue stays open; an Issue may close only when its own acceptance condition is met or its unresolved work is actually transferred to a usable successor.
- Branch/worktree cleanup follows exact content, ownership, evidence custody, active process, and dependency checks. Unknown ownership means preserve and investigate.
- The work map exposes family-level scopes. Shared indexes are integrated serially; independent evidence audits and local tests do not wait for a repository-wide semantic census.

## First execution batch

1. Use r22 as the current metadata index, then audit one family from `docs/ideas/README.md` against current Issue bodies, relevant comments, PRs, and evidence. Preserve distinct proposals and report gaps as `untriaged`.
2. Review an open PR only against its exact current head and base. Record local checks and any mandatory protection state; do not treat optional CI as a universal wait or passing checks as scientific validation.
3. Keep the XRes positive-control question scoped to PR [#9064](https://github.com/Unjuno/agent-interface/pull/9064). At head `d75f46675986108dcc8171804213d537af66748e`, its 10 reported checks passed and GitHub reported `CLEAN`, but this does not validate the measurement interpretation. Run [39158721918](https://github.com/Unjuno/agent-interface/actions/runs/39158721918) recorded the first idle-client control and raw SHA-256 `62e5fe8b2f26172a6a18d691c00781bea1e8c67d727a5b2a539c705dbaf0d54d`; it failed the expected-disconnect assertion. Run [39158819782](https://github.com/Unjuno/agent-interface/actions/runs/39158819782) preserved either observed outcome and raw SHA-256 `29b6dbf50053075de57f41b078434d45b76007e00110cf0770edcec45f353059`. In that run, the ordinary idle client and delayed owner received the same XRes `resource_base`; after owner exit the post-exit query helper reports `still_connected`. Thus the helper has not yet distinguished the retired owner from a later connection reusing that base. Preserve both raws; do not use this as a disconnect or physical-release claim. The local copies were under `%TEMP%\x11-disconnect-fence-run39158721918\x11-disconnect-fence.json` and `%TEMP%\x11-disconnect-fence-run39158819782\x11-disconnect-fence.json` on the experiment host; the workflow run links are the durable retrieval path.

4. The missing-primary-row queue includes #4, whose current body was read in full and has no comments. It is a broad open design thesis, not one implementation task. Its relation to #2/#3 and to the distinct #5 agenda is now explicit in [the durable idea index](../IDEAS_AND_OUTCOMES.md), [design-theses ledger](../design-theses.md), and [visual idea index](../ideas/README.md). Keep #4 open; no outcome or allocation is implied. This semantic read does not rewrite the frozen r15 queue or remove #4 from the separate research-index primary-row coverage gap.

The repository-wide cleanup remains in progress. This inventory refresh closed no Issue, merged no PR, deleted no branch/worktree, and did not rerun any formal allocation.
