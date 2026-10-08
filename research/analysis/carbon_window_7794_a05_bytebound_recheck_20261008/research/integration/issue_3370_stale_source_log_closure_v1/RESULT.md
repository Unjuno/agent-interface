# Issue #3613 — stale-source evidence publication closure

## H / T / D / C / U

**H.** The original experiment's 159-entry manifest and all bytes were locally
present, but the merged #3612 tree omitted 13 `.log` paths because the ignore
rule excluded them. This follow-up publishes those exact bytes without rerun.

**T.** Frozen base: `5037bb22181e1479384ef179beae307c55398937` (the #3612 merge).
The 13 source artifacts were copied byte-for-byte from the retained original
worktree, checked against their manifest byte lengths and SHA-256 digests, and
added at their original paths. No experiment code or original report was
changed.

**D.** The original manifest contains 159 entries. The baseline commit's
independent Git-tree audit found 146/159 present and matching, with exactly 13
missing and no mismatches. All 159 local source files are present and match;
the 13 omitted log paths and their expected lengths/digests are recorded in
`evidence/omitted-log-audit.json`. The final closure gate is computed from the
Git tree, not the working directory: each manifest path must exist in the
commit and its blob bytes must match both the recorded byte count and SHA-256.
Final commit/tree identifiers and counts are recorded after commit creation.

**C.** `PASS_PUBLICATION_CLOSED` only when all 159 manifest entries are in the
resulting committed tree and byte-identical. Otherwise this report must record
`HOLD_PUBLICATION_INCOMPLETE` and exact missing/mismatched paths.

**U.** Publication integrity only. This does not expand the original scoped
stale-source refusal result into model visibility, delayed/no-image,
disconnect/cancellation, or broader task-effect evidence.

## Reproduction

Run `python3 audit_git_tree.py <commit>` from the repository root. The auditor
reads each object through `git show <commit>:<path>` and compares its raw bytes
to the frozen original manifest.
