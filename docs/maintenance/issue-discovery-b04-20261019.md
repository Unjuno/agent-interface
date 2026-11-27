# Issue discovery batch B04 — routing receipt (2026-10-19)

B04 is the fourth 25-row slice of the immutable [r51 missing-primary-row queue](open-issues-missing-research-primary-row-20261019-r51.csv), rows 76–100. A live read at 2026-10-19 00:38 UTC found all 25 Issues open with no assignees. The intake read each Issue body and latest available comment for routing. It did not audit every historical comment, linked PR diff/raw packet, or branch/worktree owner. An empty assignee field does not establish that work is unclaimed.

The B04 Issues are #287, #288, #290, #294, #300, #305, #307, #315, #321, #322, #327, #332, #333, #339, #340, #344, #345, #359, #362, #364, #371, #375, #376, #383 and #389. Their outcomes are not one consolidated claim; the [idea index](../IDEAS_AND_OUTCOMES.md) preserves the distinct results and boundaries. This intake added the missing primary summaries for #375, #383 and #389.

| Research question | Issues routed | State retained |
|---|---|---|
| Delayed publication, source/read-set identity, and preservation | #287, #290, #300, #305, #315, #322, #332, #364, #375 | Git CAS, dependency completeness, non-write preservation, and candidate-path identity remain separate. #375 is a proposal with no formal measured rows; its hardlink comparison does not address in-place mutation. |
| GUI selection checks and target binding | #288, #294, #321, #327, #333, #371, #383 | Preserve the failed/limited visual guards, readiness result, and post-check selection race independently. #383 passed its scoped race audit; this does not make screenshot checks atomic or establish general application behavior. |
| Accessibility transport and object identity | #339, #362, #376, #389 | The explicit-address transport gaps and unavailable selection identity remain bounded to their tested topology. #389's standard Registry positive control passed; it establishes event transport only, not document-object identity. |
| Delivery semantics | #345, #359 | Identical-request idempotency passed in local SQLite; same-ID/different-content conflict remains frozen without a formal result. |
| Other bounded questions / corrections | #307, #340, #344 | Keep the duplicate-formal correction, failed live-placement gate, and scoped native SVG results distinct. |

## Linked PR freshness spot-check

The 22 PRs explicitly linked from the B04 Issues were checked live: #251, #277, #289, #291, #296, #304, #306, #319, #324, #329, #334, #337, #338, #357, #358, #369, #378, #382 and #407 are **MERGED**; #293, #353 and #370 are **CLOSED without merge**. This checks only these cited PRs, not the repository's full PR queue or all branches that may touch these Issues.

No Issue or PR state changed, and no experiment was run or relabeled. Before a worker takes one of these topics, it must check current PR heads, registered worktrees, local owner/process context, exact source revision and any unique raw custody. Use a distinct output path and do not edit the shared idea index concurrently with another integrator.
