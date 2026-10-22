# Read-only Git worktree custody census r01 (2026-10-22)

Captured 2026-10-22 03:12:37 UTC against local `origin/main` `178983ac3cb884f19536810ce56b53d79122090a`. This inventory describes one Codex task-root checkout family on one Windows host; it is not a portable or repository-wide process census.

## Result

`git worktree list --porcelain` returned 45 existing linked worktrees. `git status --porcelain --untracked-files=all` found 14 with uncommitted entries and 31 clean; no listed worktree path was missing. Comparing each recorded HEAD against `origin/main` gave the base-only and worktree-only commit counts below. A read of all open PR head names found no exact branch-name match for these 14 dirty worktrees.

A status-entry count is the number of porcelain records, not necessarily a count of distinct files or meaningful edits. Clean status does not imply that a branch has no unique commits. No reset, checkout, archive, deletion, or file inspection of the dirty worktrees was performed. Custody/owner remains unresolved; preserve the changes until ownership and recovery are confirmed.

| Relative worktree | Branch | HEAD | Status entries | Main-only commits | Worktree-only commits |
|---|---|---|---:|---:|---:|
| `work/agent-interface` | `integration/x11-fake-socket-relay-r01` | `994f18dcd479eca0885e979749db30073a98f3a2` | 111 | 313 | 1 |
| `work/goal-computer-control-next-20261020` | `research/57-release-supervisor-bound-20261020` | `53186c391103d50cb0b7555165a174a15842f586` | 9 | 143 | 0 |
| `work/mindustry-current-main-audit-20261005` | `research/57-compiled-efficiency-v2-20261005` | `31095132d080413143823862c6ec0eca8fb39e52` | 92 | 2,510 | 0 |
| `work/pr8842-evidence-r01` | `rescue/pr8842-evidence-r01` | `46dc02dc4a718b832ba768a82b17ef9d9fbcc252` | 1 | 215 | 2 |
| `work/repo-cleanup-r71-20261019` | `research/xres-wire-fake-relay-r01` | `627223a9724757e226307f3f7afa86338b3b82ad` | 1 | 280 | 0 |
| `work/repository-cleanup-plan-r01-20261020` | `research/owned-cancel-supervisor-prototype-r01` | `24e5fbd0823f0a8adbbad85830da2e639b8ecc91` | 18,407 | 89 | 7 |
| `work/repository-consolidation-20261019` | `test/xorg-xres-disconnect-fence` | `4ffa711d6bf4a5e60f18109dc779ed753eff4f88` | 6 | 461 | 5 |
| `work/repository-consolidation-current-20261019` | `integration/57-composition-plan-20261020` | `577ddc30c918c422ddebab8a12eb133649fc789a` | 1 | 179 | 0 |
| `work/repository-inventory-r20-20261019` | `docs/repository-inventory-r20-20261019` | `5ae50f1a8f77438e1e2dc52548b2e9da9c6db285` | 9 | 292 | 1 |
| `work/standard-caller-blocked-x11-a04-20261019` | `research/standard-caller-blocked-x11-a04-20261019` | `95386ee7e10e7ffc7422bd473f4db29991bd28b6` | 5 | 291 | 0 |
| `work/stdio-cancel-output-backpressure-20261020` | `test/stdio-cancel-output-backpressure-20261020` | `3f8406516747304fe82d03a7d09cfed86ea9cd91` | 8 | 176 | 0 |
| `work/x11-proxy-fake-relay-20261019` | `research/x11-proxy-fake-relay-20261019` | `f9e3f1d72e06aa3fe717c46fdba5186a8e48cf2c` | 3 | 329 | 0 |
| `work/x11-release-worker-receipt-r01` | `fix/x11-release-worker-receipt-r01` | `e88c42083fa81d811fd14787b918bae34d818282` | 30 | 109 | 9 |
| `worktrees/primary-mint-sparse` | `feat/prestarted-cancel-supervisor-r01` | `76626da8b03df25024d12efb5f1dde2f12c53ed2` | 5,151 | 84 | 21 |

The two largest entries are concentrated under `research` (17,851 entries in `work/repository-cleanup-plan-r01-20261020`; 5,140 in `worktrees/primary-mint-sparse`). `work/mindustry-current-main-audit-20261005` has 92 entries under `research`. This census did not inspect their contents, so it cannot distinguish raw outputs, generated files, profile data, or source changes.

## Next bounded custody action

Resolve owner and recovery evidence for `work/repository-cleanup-plan-r01-20261020` and `worktrees/primary-mint-sparse` first, then the 12 smaller dirty worktrees. Match live Codex task/worktree attachments, Issue/PR lineage, branch-only commits, and unique file content. Record a resume/transfer/archive disposition for each. Unknown ownership or recoverability means retain and investigate; do not treat these as safe deletion candidates.

Commands used: `git worktree list --porcelain`; per-worktree `git status --porcelain --untracked-files=all`; `git rev-list --left-right --count origin/main...<HEAD>`; `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number,headRefName`.