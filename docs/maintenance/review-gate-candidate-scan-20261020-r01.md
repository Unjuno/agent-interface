# Review-quorum candidate scan r01 — 2026-10-20

## Scope and method

Read-only scan of open PR metadata and bodies from `Unjuno/agent-interface` on
2026-10-20, while local `origin/main` was
`b38e49f8cf5cef3a30f33e945bf71feca838eae0`. `gh pr list --state open --limit
1000 --json number,title,isDraft,headRefOid,author,body` returned 477 PRs.
The scan searched for explicit body markers: `required_nonauthor_content_votes`,
threshold 2, two-nonauthor approval, nonauthor quorum, or a fixed nonauthor
committee. Thirty-nine records matched; all 39 were Draft at the read time.

This is a **candidate screen only**. A word match does not prove a currently
operative requirement, that the PR is mergeable, or that its source Issue is
resolved. PR authors can include scoped scientific-review or audit controls;
those controls must be read in context and retained when they validate a
research claim. This scan does not update or close any PR, request reviewers,
change a branch, rerun an experiment, or release an allocation.

The live GitHub API read for `main` branch protection returned `404 Branch not
protected`; the repository rulesets list was empty. Thus the matched body text
does not establish a repository-wide GitHub protection rule. PR #7283 is a
confirmed example of a body-level fixed quota: its open Draft body specifies
“two genuine nonauthor fixed-content approvals” and names three prospective
review seats. That is separate from its technical tests, current-base
applicability, platform/owner/cancellation, and sole-sender checks. Preserve
those correctness conditions while removing any stale reviewer-seat/count
requirement from current operating instructions.

## Candidate PRs

The following are the exact 39 body-marker matches. Each remains a separate
disposition; no merge, close, or cleanup action is inferred from this list.

| PR | Head at scan | PR | Head at scan | PR | Head at scan |
|---:|---|---:|---|---:|---|
| #8371 | `e88a240fdb2da5cb21410a4c...` | #8368 | `ad2e3a34b4a165d0a3ca542...` | #8320 | `fd14d9ed655192b90c38c850...` |
| #8275 | `781c65dad13b1b14157c1dfe...` | #8261 | `4190104d0c72a025093c8569...` | #8164 | `0b1187d20000aabdc63ce8a...` |
| #8139 | `9648fc1dc6f68fa6702afb4d...` | #8031 | `78da45acb3b1aff7200a66e6...` | #7992 | `1cce7ab8c0fdd96dc9f1e543...` |
| #7509 | `e7fcd4e3427178d71846db8f...` | #7496 | `eeb3424686affb890cbe57f0...` | #7314 | `c103244a5f68c957fd2261ed...` |
| #7311 | `d2b3311b5eac30774a9e698...` | #7290 | `be60e9c0ab1bccf3770c7760...` | #7283 | `92a610b30507e9ac0c159ca1...` |
| #7279 | `ea8134de00bf2c43dfa6dfff...` | #7254 | `16a2f9083683745c5ad3bed2...` | #7244 | `8a518578991988ddb463d512...` |
| #7239 | `a51bf794803577e41a587e72...` | #7237 | `41baeb135ef42a4094eff606...` | #7232 | `fdb62ff778b4dd6253eec853...` |
| #7231 | `1ee3a70d1ae5518082ee6d40...` | #7224 | `6be47553a41a06e8e1aa7041...` | #7218 | `6c700696cef58ad7273223fd...` |
| #7207 | `027474790c7b69a39448b317...` | #7201 | `461b0f4306ec16c007d4971b...` | #7196 | `a7265025cbedc9ba5c30fb0b...` |
| #7189 | `81919ebf81fb664ec2077066...` | #7186 | `49b03b52e90230234225c84c...` | #7176 | `3276a4a390f0c467de3f195a...` |
| #7168 | `bac0f9effbddeccf34e3a30b...` | #7140 | `b8a2209f76aec759cc58d770...` | #7139 | `0da290e06cf1ed433d779688...` |
| #7125 | `6353a588c292f009a3fc2203...` | #7120 | `be6c57bf961480723c615ea4...` | #7094 | `506a0a47fc643af7add7a3a9...` |
| #7088 | `453ca58746c93d55c2a433b7...` | #7087 | `6bdd04b75f887d60497f4426...` | #7062 | `6f79681e5dc5681c984543c0...` |

Heads are abbreviated for navigation and are not sufficient for a state
change. Fetch each full current head and base before editing its body or
deciding its disposition.

## Next bounded action

Review the #59/#57 subset first, starting with the latest live heads among
#8371, #8368, #8275, #8261, #8164, #8139, #8031, #7992, #7509, #7283, #7279,
#7254, #7232, #7224, #7196, #7176, #7168, #7140, #7139, and #7125. For each,
separate technical acceptance conditions from fixed reviewer-seat/quorum
language, verify source evidence and superseding work, then either remove the
obsolete quota text while retaining substantive checks or record why the
item-specific acceptance requirement remains current. Keep distinct PRs and
research outcomes separate. No PR status change follows automatically.
