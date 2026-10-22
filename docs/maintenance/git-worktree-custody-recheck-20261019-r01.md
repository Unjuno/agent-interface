# Git worktree custody recheck r01 — 2026-10-19

Read-only check captured at `2026-10-18 23:20:43 UTC`, against main
`237915de7886535a599343c9cd8331787d556c50`. `git worktree list --porcelain`
reported 12 registered worktrees: 11 clean and one with two untracked
directories. An exact branch-name comparison found no current open PR whose
head names one of these worktree branches. This check does not establish worker
ownership or exclude dependencies expressed through other branch ancestry.

| Workspace label | Branch / tip | Observed state | Custody disposition |
|---|---|---|---|
| `agent-interface` | `main` / `237915de7886` | Clean | Canonical checkout. |
| `outputs/pr7370-independent-review` | detached / `aebf4ac28a84` | Clean | Retain pending owner/session and purpose confirmation. |
| `outputs/pr7660-independent-test` | detached / `279577b515b2` | Clean | Retain pending owner/session and purpose confirmation. |
| `outputs/pr7660-independent-test-current` | detached / `6d3b1017fc29` | Clean | Retain pending owner/session and purpose confirmation. |
| `work/mindustry-current-main-audit-20261005` | `research/57-compiled-efficiency-v2-20261005` / `31095132d080` | Two untracked directories; no tracked diff | PR [#7856](https://github.com/Unjuno/agent-interface/pull/7856) is merged and its head equals this branch tip. Each untracked directory is an Edge profile named `interface-edge-frame-ocr-*`; each contains 47 files, together 3,030,147 bytes. Names and metadata only were inspected. Last-write times were 2026-10-05. A process command-line scan found no non-audit process referencing these directory names, but does not establish ownership or that the profiles are disposable. **Quarantine / owner unknown; preserve.** |
| `work/release-expiry-queued-press-mcp` | `runtime/fake-x-release-order-followup-20261019` / `38300c7275ad` | Clean | Retain pending owner/session and PR-stack dependency review. |
| `work/repository-consolidation-20261019` | `test/xorg-xres-disconnect-fence` / `4ffa711d6bf4` | Clean | Retain pending owner/session and PR-stack dependency review. |
| `work/repository-inventory-r21-20261019` | `docs/repository-inventory-r21-20261019` / `e8ffb8cca024` | Clean | Retain pending owner/session confirmation. |
| `work/xres-18s-observation-run-20261019` | `docs/xres-18s-observation-run-20261019` / `16e69150d1ae` | Clean | Retain pending owner/session confirmation. |
| `work/xres-idle-client-control-20261019` | `test/owned-xres-pid-cancel-composition-20261019` / `2affa665218a` | Clean | Retain pending owner/session and PR-stack dependency review. |
| `work/xres-post-horizon-bound-20261019` | `test/xorg-xres-post-horizon-bound-20261019` / `d3dd3152206d` | Clean | Retain pending owner/session and PR-stack dependency review. |
| `D:/codex-v39-pending-main-a01-20261008` | `research/59-v39-pending-invalidation-currentmain-20261008` / `cae208b3ab11` | Clean | Retain pending owner/session and PR-stack dependency review. |

Clean means no tracked or untracked Git changes at the snapshot; it does not
mean stale or safe to remove. The next finite cleanup step is to identify the
owner and evidence role of the two Edge profile directories in the #7856
worktree. Preserve them until their raw-data relationship and recovery path are
known. After that, review the ten noncanonical clean worktrees for exact open
PR bases/commit dependencies and owner/session custody. No worktree, branch, or
artifact was removed by this recheck.
