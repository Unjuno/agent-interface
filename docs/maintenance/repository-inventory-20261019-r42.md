# Repository membership delta r42 — 2026-10-19

Captured at `2026-10-18 22:37:50 UTC` from complete paginated `gh issue list`
and `gh pr list` responses for `Unjuno/agent-interface`. The inspected main
tip was `76ed0ee86dec7e9f8468863eaf9e682abb51d36b`.

| Surface | Open count | SHA-256 of sorted numeric IDs (UTF-8, LF after each ID) |
|---|---:|---|
| Issues | 1,675 | `4D45620D8AAE450E7F37C9C7A0D2B183534C44094C117671362B12BB11751678` |
| Pull requests | 505 | `9A86566E84DCB7E6F89C957ECCC358E02879322DE434470777A006A09B6C24CC` |

Compared with [r41](repository-inventory-20261019-r41.md), the complete Issue
ID set is unchanged. The only open-PR ID addition is [#9099](https://github.com/Unjuno/agent-interface/pull/9099); no PR ID was removed. The fresh
metadata fields for unchanged entries are not recopied here; r41 retains the
last full metadata snapshot, and this note records the membership delta.

At the captured read, #9099 was open at head
`25efcad1c6e494b1212d68f38ea1e376011cc810`. Its private-Xvfb
`x11-integration` check had failed in the new standard-caller test while reading
`observer.display.info.release` (`AttributeError` in Python-Xlib). Other checks
were still running or had passed. This is a concrete repair-and-recheck item,
not a merge/close disposition. Preserve the failed run and its uploaded raw
artifact before recording a corrected attempt.

This is membership plus one failed-check observation, not semantic triage,
ownership verification, or a complete PR review. Counts and metadata do not
authorize Issue closure, PR merging, branch/worktree deletion, or artifact
cleanup. Recheck the live item and current owner before those actions.
