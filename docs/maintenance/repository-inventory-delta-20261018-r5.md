# 2026-10-18 open Issue/PR inventory refresh r5

Snapshot time: 2026-10-18 12:24 UTC. Source: all pages of the GitHub REST open Issue and Pull Request endpoints for `Unjuno/agent-interface`. The Issues endpoint returned 17 pages after excluding PR-shaped entries; the Pull Requests endpoint returned 6 pages.

| Set | Previous r4 | Current r5 | Entered open set | Left open set |
|---|---:|---:|---|---|
| Issues | 1,677 | 1,676 | none | #8386 |
| Pull requests | 521 | 515 | none | #7521, #9005, #9008, #9009, #9011, #9012 |

The full metadata snapshots are [open Issues](open-issues-20261018-r5.csv) and [open Pull Requests](open-prs-20261018-r5.csv). Their SHA-256 digests are:

- Issues: `989759a0f91e5f6dc8efbd1f4b4684d7f13b431a31fd1234068607f77d91c62d`
- Pull Requests: `d323c7399f0fc4b8fbae6a7fff44ae2a157232abb4a5ed7e05eb0139a4530675`

The only issue that left the open set, #8386, is now closed with GitHub `state_reason=completed` (closed 2026-10-17 03:47:23 UTC). No Issue status changed in the cleanup batch recorded here. This snapshot does not semantically classify all 1,676 open Issues.

The six PR transitions are distinct:

- #7521 closed unmerged as the duplicate model-economics implementation line; #8772 remains the identified successor, with current-main follow-up still required. The earlier family disposition is recorded in [`REPOSITORY_CONSOLIDATION.md`](../REPOSITORY_CONSOLIDATION.md).
- #9005 closed unmerged. Its head `880c6b63036fa297d4a5c0a68498edf94e1b48d4` is an ancestor of the current main history and has zero diff against main, so its model-evaluation idea notes remain preserved. The remote branch is absent.
- #9008 merged at 2026-10-18 12:21:57 UTC as `c95caacce56925a03fb5724b6559506fcdac2050`.
- #9009 merged at 12:15:50 UTC as `996912adfc33237a3312f39f860f82b21819f51c`.
- #9011 merged at 12:07:54 UTC as `5dc27cff7ffed6fb218719ddc53b95a901e03d0c`.
- #9012 merged at 12:00:55 UTC as `eb9ff79b5e252eb4f54619f49b5b9ef0c6f458ad`.

PR #9018 was opened after the r4 snapshot and merged at 12:11:11 UTC as `c71cedb20a46b36947f91828f1e84641d083deb5`; it documents the #9011 merge and inventory update. It therefore does not appear as an entered or exited PR in the r4-to-r5 open-set delta.

For #9008, the synchronized head retained the added soft-typed-evidence regression, corrected its stale test SHA in `PAIR_RECOVERY_SHA256SUMS.txt`, and verified both experiment manifests against Git blob bytes (29/29 and 14/14). The saved pair-recovery audit passed; the retained trace replay passed 1/1 in normal and optimized Python. This is offline trace evidence only. Issue #59 remains open because live game/input/effect behavior is not established.

The transitions reduce the open PR count; they do not establish repository-wide cleanup. The next work remains one research family or PR at a time, preserving evidence and keeping unresolved hypotheses open.
