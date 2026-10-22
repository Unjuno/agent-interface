# Open PR disposition audit r01 — 2026-10-20

This receipt records a bounded read-only audit of nine open PRs against the
then-current `origin/main` `c2f0cd874ce50af310a071b3df98ca52eba7b057`.
The audit examined the exact PR heads, diff scope, available checks, comments,
evidence packages, and known Issue/PR dependencies. It changed no GitHub state
and did not rerun any consumed experiment or candidate/auditor pair.

## Dispositions

| PR | Evidence and defect | Safe next step |
|---|---|---|
| [#8702](https://github.com/Unjuno/agent-interface/pull/8702) | Draft A07 raw-custody reconciliation reports 2,358 files and ten cancellation records, but its private raw manifest/event stream is absent from the PR and inspected worktrees. The result explicitly remains HOLD; merged #9181 verifies tracked package identity, not the private raw claims. | Preserve as author-reported. Resume only if an authorized custodian supplies unchanged raw or a privacy-approved verification manifest. Never rerun A07 for this audit. |
| [#8848](https://github.com/Unjuno/agent-interface/pull/8848) | Draft A12 soft-ammo feedback construction. Independent byte check found 7/19 `SHA256SUMS` entries match CRLF-converted bytes rather than retained LF blobs; the audit script does not verify the manifest. It has one saved WSLc run and no live Doom/task-effect claim. | Repair hashes from exact retained bytes and rerun only the non-executing custody audit; preserve all saved run/result bytes. Recheck exact head/base and checks before disposition. |
| [#8843](https://github.com/Unjuno/agent-interface/pull/8843) | Draft A10 synthetic cancel-order construction, with the same class of 7/19 CRLF-vs-LF manifest mismatch. Its saved result is construction-only and explicitly excludes live GUI/input, physical release, recovery, and task outcome. | Repair the manifest from exact retained bytes and rerun only non-executing custody checks. Do not rerun WSLc or the experiment. |
| [#8845](https://github.com/Unjuno/agent-interface/pull/8845) | Draft A11 authored-ammo boundary package; stale base `f185a905…`, replay gate passes, formal check skipped. Its deviation note says there was no live game allocation, but it does not reconcile its `wslc run` with the then-existing shared WSLc ownership/no-call gate. | Preserve the frozen construction. Resolve whether separate owner clearance existed; add an additive deviation record if it did not, then retarget and check current-main integration without rerunning the experiment. Keep #59 open. |
| [#8844](https://github.com/Unjuno/agent-interface/pull/8844) | Draft A04 candidate 1/1, auditor 1/1 failed before summary; disposition is `HOLD_UNCERTAIN`. The first mismatch is a near-singular image detector causing the ViewState oracle to yield. Its archive SHA and 2,198-file custody were independently recomputed. | Preserve the exact frozen packet and HOLD. Retarget/reconcile additively and link the family result; any new candidate/auditor run requires a distinct fresh allocation. |
| [#8840](https://github.com/Unjuno/agent-interface/pull/8840) | Non-draft A03 candidate 1/1 exit 0 over 360 trials; auditor 1/1 failed before summary, so HOLD_UNCERTAIN. The report checksum has a one-character typo and `analysis-index` fails because the generated result index is stale/missing. Correct blob hash: `60d6d0ae0b04ef58c006fef14b053dfda0c8077350510ac7e36f7c6541a1f229`. | Add a source-safe checksum erratum (updating the manifest if the hashed report changes), regenerate the index from current main, and rerun only analysis-index/replay checks. Never rerun A03. |
| [#8841](https://github.com/Unjuno/agent-interface/pull/8841) | Draft synthetic monitor-boundary evidence is valid within scope but does not establish #59 live threat exposure or task success; it is based on stale `f185a905…`. | Preserve as scoped evidence. Integrate only through a current-main evidence successor with exact-head indexes/checks. |
| [#8836](https://github.com/Unjuno/agent-interface/pull/8836) | `FAIL_COST_GATE_SCOPED`; the corrected accounting is 96 vs 136 and the strict `release_required` condition is omitted. Existing checks are old and based on stale `f185a905…`. | Preserve the negative result unchanged. A successor may repair the accounting record and prove current-main integration without rerunning the consumed experiment. Do not merge as-is. |
| [#8832](https://github.com/Unjuno/agent-interface/pull/8832) | Bounded null result `NO_INCREMENTAL_VALUE_SCOPED`; `test_audit.py` reads a private absolute path (`/private/tmp/.../gold.json`), so a clean checkout cannot reproduce the audit. The saved result itself is not implicated. | Repair only the test fixture path in a successor, run the focused tests normally and under `-O`, and regenerate exact-head indexes. Preserve `results/AUDIT.json`; do not rerun reviewers or the experiment. |

## Summary and routing

None of these nine PRs was verified as merge-ready by this audit. That is not a
recommendation to close them: each has a distinct retained result, a concrete
repair/reconciliation condition, or an unresolved custody dependency. Issue
#59 remains open; these packages do not establish MAP01 success, general live
computer control, physical release, or matched efficiency.

The finite repair candidates are #8848, #8843, #8840, and #8832. Keep each
repair in an isolated successor or exact PR branch, preserve frozen raw/results,
rerun only the non-executing checks named above, and re-read the live PR state
before any merge/close decision. Shared family indexes should be updated only
after the respective evidence is reconciled. The unresolved owner/custody and
allocation conditions for #8702/#8845/#8844 remain explicit HOLDs.
