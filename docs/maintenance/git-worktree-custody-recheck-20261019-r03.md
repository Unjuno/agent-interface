# Git worktree custody recheck r03 — 2026-10-19

Read-only snapshot of the repository's registered Git worktrees at approximately
2026-10-19 05:32 UTC. The documentation checkout used for this audit was clean at
`95386ee7e10e7ffc7422bd473f4db29991bd28b6` immediately before this report was
added. Local paths are represented by their directory names; no files were
moved, reset, archived, or deleted.

| Worktree directory | Checked-out branch | HEAD | `git status` entries | Untracked entries |
|---|---|---|---:|---:|
| `agent-interface` | `integration/x11-fake-socket-relay-r01` | `994f18dcd479` | 46 | 0 |
| `pr7370-independent-review` | detached | `aebf4ac28a84` | 0 | 0 |
| `pr7660-independent-test` | detached | `279577b515b2` | 0 | 0 |
| `pr7660-independent-test-current` | detached | `6d3b1017fc29` | 0 | 0 |
| `mindustry-current-main-audit-20261005` | `research/57-compiled-efficiency-v2-20261005` | `31095132d080` | 92 | 92 |
| `release-expiry-queued-press-mcp-20261018` | `runtime/fake-x-release-order-followup-20261019` | `38300c7275ad` | 0 | 0 |
| `repo-cleanup-r71-20261019` | `docs/repository-consolidation-sync-20261019` | `95386ee7e10e` | 0 | 0 |
| `repository-consolidation-20261019` | `test/xorg-xres-disconnect-fence` | `4ffa711d6bf4` | 6 | 3 |
| `repository-inventory-r20-20261019` | `docs/repository-inventory-r20-20261019` | `6a00e00487ab` | 0 | 0 |
| `repository-inventory-r21-20261019` | `docs/repository-inventory-r21-20261019` | `e8ffb8cca024` | 0 | 0 |
| `standard-caller-blocked-x11-a04-20261019` | `research/standard-caller-blocked-x11-a04-20261019` | `95386ee7e10e` | 5 | 5 |
| `x11-proxy-fake-relay-20261019` | `research/x11-proxy-fake-relay-20261019` | `f9e3f1d72e06` | 3 | 2 |
| `xres-18s-observation-run-20261019` | `docs/xres-18s-observation-run-20261019` | `16e69150d1ae` | 0 | 0 |
| `xres-idle-client-control-20261019` | `test/owned-xres-pid-cancel-composition-20261019` | `2affa665218a` | 0 | 0 |
| `xres-post-horizon-bound-20261019` | `test/xorg-xres-post-horizon-bound-20261019` | `d3dd3152206d` | 0 | 0 |
| `codex-v39-pending-main-a01-20261008` | `research/59-v39-pending-invalidation-currentmain-20261008` | `cae208b3ab11` | 0 | 0 |

The snapshot contains 16 registered worktrees: 11 with no reported changes and
five with 152 status entries in total, including 102 untracked paths. Of the 50
tracked changes, 46 are in `agent-interface`, three in
`repository-consolidation-20261019`, and one in `x11-proxy-fake-relay-20261019`.
All 102 untracked paths occur in `mindustry-current-main-audit-20261005`,
`repository-consolidation-20261019`, `standard-caller-blocked-x11-a04-20261019`,
and `x11-proxy-fake-relay-20261019`.

The 13 checked-out local branch names were compared with all open PR head refs in
the complete r70 metadata; there were no exact matches. Three worktrees are on
detached HEAD. `git worktree list` reported none locked or prunable. These facts
do not establish that a tree is unused: PRs can depend on branches as bases,
detached trees can contain unique review work, and clean trees can preserve
needed results. The normal status command does not show ignored files. This
snapshot does not inspect running processes, worker/session ownership, open PR
base dependencies, or ignored-file contents. Keep all worktrees until those
relations and recovery paths are resolved individually.
