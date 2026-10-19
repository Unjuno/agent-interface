# Repository open-work membership recheck r84 — 2026-10-19

Captured at 2026-10-19 07:50 UTC from complete GitHub API pagination for
`Unjuno/agent-interface`, at main
`9a91dd2f24193831b6320f24278f5e8d8a1048e2`.

| Surface | Current open count | Membership comparison | Evidence |
|---|---:|---|---|
| Issues | 1,673 | Same IDs as r70 | REST pagination of open Issues, excluding pull-request records; exact set comparison with the r70 CSV. GraphQL open count agrees. |
| Pull requests | 484 | r70 minus five; no additions | Complete REST pagination and exact set comparison with the r70 CSV; GraphQL open count agrees. |

The five PRs no longer open are #8794, #8798, #8803, #8811, and #8825. The
first, second, third and fifth are merged; #8811 is closed. This reproduces the
r83 membership result on the newer main SHA. The immutable [r70 inventory](repository-inventory-20261019-r70.md)
remains the latest full row-level metadata snapshot; this recheck does not
duplicate its CSV files.

## Scope and next work

Membership does not classify the 1,673 Issues or review the 484 PRs. It does not
establish current authorship, worktree custody, readiness to merge, or
permission to delete refs. Do not infer that an unassigned or old Issue is
disposable.

The first semantic family refresh compared live Issues [#6](https://github.com/Unjuno/agent-interface/issues/6)
and [#56](https://github.com/Unjuno/agent-interface/issues/56) with their
canonical [family record](../ideas/reactive-macro-symbolic-interface.md). The
record accurately keeps #6's broad reactive-control menu distinct from #56's
planner-authored symbolic-interface question, preserves the scoped A05, R02,
A14 and #7616 limits, and points to the actual unresolved adoption comparison.
Both Issues remain open; no outcome or allocation was changed, and no formal
experiment was rerun. Their existing `keep-open/actionable` status is appropriate
until a finite matched-correctness comparison is available or the question is
explicitly superseded with its idea and evidence preserved.

Next, continue with one non-overlapping family batch from the current work map:
classify each Issue by its distinct question, evidence, dependency/ownership and
finite next discriminator before any closure. Integrate shared index edits one
at a time. Keep open work that needs an experiment, integration decision or
custody resolution; catalog-only ideas may be individually closed only after
their canonical entry and re-opening path are recorded on the source Issue.
