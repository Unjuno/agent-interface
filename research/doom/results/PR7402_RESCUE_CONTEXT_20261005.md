# PR #7402 retained-time analyzer evidence rescue

## H / T / D / C / U

- **H:** The closed PR contains useful, reproducible construction evidence for a release-order guard in the retained-input analyzer. Its result must remain narrowly scoped because an additional mutation disclosed later in the PR discussion was not covered by the saved six-test pass.
- **T:** Preserve the exact A01 pre-container STOP, A02 pinned/offline WSLc test record, both original audit scripts/results, and the adjacent owner-thread extension note. Re-run only each saved-result audit in an isolated scratch extraction; do not rerun the consumed candidate/container experiment.
- **D:** A01 stopped before test process/container creation because the bind-source argument was invalid. A02 reports six analyzer tests passing in the pinned Python image with network disabled and a read-only checkout. The recorded runtime warned that swap limits were unsupported. Both saved audit scripts pass when replayed against scratch copies, and their generated JSON is semantically equal to the retained `AUDIT.json`.
- **C:** The checks exercise synthetic timestamps and saved files, not X11, a game, or live control. A later exact-head mutation probe in [PR #7402 discussion](https://github.com/Unjuno/agent-interface/pull/7402#issuecomment-5976134858) found that the candidate analyzer could accept JSON `false` as `valid_until_ns` when both compared values were changed together. Therefore the saved 6/6 result is not evidence that this malformed-deadline case is handled.
- **U:** No live X server, hardware transition, application consumption, game feedback, recovery, MAP01 effect, or strict total-memory limit is established. This rescue adds evidence only; it does not merge the closed PR's runtime/analyzer edits or claim that the later false-deadline defect is fixed on main.

## Provenance and integrity

- Source: closed, unmerged [PR #7402](https://github.com/Unjuno/agent-interface/pull/7402), head `d54efecdd28c2d0375bd1443f38db4d99a7b8062`.
- The 14 files under the A01/A02 result directories and the owner-thread extension note are copied byte-for-byte from that head. The experiment records remain at their original paths; this context is an additive reconciliation note.
- The offline audit replay was run from an isolated `git archive` scratch extraction. The audit scripts write their JSON output only in scratch; the preserved source records were not rewritten.
- The original PR was closed unmerged while its base stack was itself closed/unmerged. Its branch has no current open PR dependents. Runtime edits were not transplanted because they were part of that stale stack and the later malformed-deadline mutation was a red counterexample requiring a separately reviewed fix.
