# Local workspace custody census — 2026-10-19

This is a read-only metadata snapshot of the current Codex workspace's top-level
`work/` directory. It is separate from the tracked contents of
`Unjuno/agent-interface`; it does not establish that any item is stale, unused,
owned by the current worker, or safe to remove.

## Snapshot

- 190 top-level directories and 341 top-level loose files.
- 6 directories have `.git` metadata; 184 are non-Git artifact directories.
- The 184 non-Git directories contain 5,230 files totaling 303,118,316 bytes
  (about 289 MiB), based on recursive file lengths at capture time.
- `git worktree list --porcelain` reports 8 registered worktrees across the
  workspace, including checkouts outside `work/`. Worktree registration is a
  separate count from directories containing `.git`.
- The attached [CSV](workspace-custody-census-20261019.csv) lists every
  top-level directory and loose file with relative path, file count, byte count,
  last-write time, extension counts, and up to three sample filenames. It does
  not copy file contents or hash individual artifacts. CSV SHA-256:
  `460d5a63f673117510f9220087222d31789f38dfb20aa95f84721775fa8a4f60`.

## Safe disposition process

Review the CSV in small batches. For each entry, link it to a worker/session,
Issue or PR, canonical evidence path, and any unique raw/result. Then record one
of these states in the follow-up ledger:

| State | Meaning |
|---|---|
| `retain-canonical` | Current source or evidence belongs here. |
| `retain-history` | Superseded or failed result remains useful provenance. |
| `merge-verified-duplicate` | Contents and hashes were compared; canonical copy and references are recorded. |
| `quarantine-owner-unknown` | Provenance or active use is unknown; preserve without treating it as available work. |
| `eligible-for-removal` | Owner, active use, preservation, recovery, and references were verified. This is eligibility, not deletion. |
| `unreviewed` | No disposition evidence yet. |

Before moving an item, record source and destination, content hash, linked work,
and a successful read-back from the destination. Before removal, additionally
confirm no active process/session, worktree, PR, or unique experiment depends on
it. Never infer ownership or staleness from age, naming, lack of `.git`, or an
empty assignee field. This census authorizes no deletion and no change to remote
Issue/PR state.

## Limits

The scan is a one-time local snapshot. Timestamps are filesystem metadata,
directory sizes may change during concurrent work, and this report makes no
claim about other workers' machines or all GitHub refs. Refresh the census
before making a disposition decision.
