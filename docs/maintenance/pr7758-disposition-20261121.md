# PR #7758 current disposition — 2026-11-21

PR [#7758](https://github.com/Unjuno/agent-interface/pull/7758) remains an
open draft for Issue [#7728](https://github.com/Unjuno/agent-interface/issues/7728).
This note records its state against current `main`
`b5c7dff376b244e13987dcf724c12fcac47c328c`; it does not revise the historical
sensor records or authorize a rerun.

## Current facts

- GitHub reports the PR head `f7f8fc24c1d8a0a744b154d9543414da8242c4c1`, base
  `c520359ee10b8071d13f2e93e82bd840a81eabda`, `draft=true`, and
  `mergeable_state=DIRTY`. It is four commits ahead of its October base, while
  current main has advanced far beyond that base. The merge-base comparison is
  still the PR's original base; current-main comparison is diverged and GitHub
  does not offer a clean merge.
- The 31-file evidence addition remains independently scoped to the two Windows
  counter packets and the analysis index. It contains no task-route comparison
  or application effect result.
- The retained A01 and A02 audit unit tests were extracted read-only from the
  exact PR head into a temporary directory and run on Windows CPython 3.11.9:
  3/3 pass normally and 3/3 pass under `-O` for each audit package. This verifies
  only the synthetic raw/auditor contracts; it does not reopen either sensor
  capture or resolve the existing holds.
- The extracted test-file bytes match the PR's A02 `SHA256SUMS` pin
  (`cca7bf90cf927aa8b5a86bccda66a9c4c93b68a6229197a2200a8b503393f668`). The
  A01 test hashes to `353afdb4a6a8e2f320774ad297997307e3bad74c64307ed604bbd21ca7a92378`;
  no independent frozen expected test hash was listed for that file. The
  auditor modules were loaded from the same exact PR head. Temporary extraction
  did not touch the checkout or sensor state.
- A01 remains `PASS_COUNTER_ORACLE_MATCH` with
  `HOLD_RUNNER_SOURCE_BYTES_UNRECOVERED` (5/6 frozen source blobs match).
  A02 remains `PASS_SIX_SAMPLE_COUNTER_ORACLE_MATCH` with
  `HOLD_BASE_SNAPSHOT_STALE` (7/7 frozen source blobs match, but the frozen
  local main was already behind GitHub main). Their raw/audit hashes are
  preserved; no candidate was rerun and no freeze was edited.
- The PR body asserts a requirement for two explicit approvals. Current
  `Worker Quickstart` says ordinary authorized work must not require an invented
  reviewer quota, and GitHub reports no classic protection or rulesets. This
  discrepancy should be corrected if the PR is revived. It is not the present
  integration blocker: the PR is stale, merge-conflicting, and scientifically
  HOLD.

## Disposition

Keep the PR and Issue open with the sensor-only results and provenance holds.
Do not merge the old head, retarget it by mechanically merging current main, or
repeat either one-shot sensor observation. If the family is resumed, create a
small successor that imports the historical packets unchanged, updates only
navigation and current-state metadata, removes the unsupported reviewer-quota
wording, and locally verifies the resulting evidence tree. Any new meter
eligibility or route/effect experiment needs its own current-main preregistration
and must preserve the prior A01/A02 outcomes as historical evidence.

This record does not qualify meter resolution, idle baseline, application
effect, energy per verified effect, T0, or T1. Issue #7728 remains actionable;
the eventual successor depends on an eligible instrument and a separately
verified task-effect oracle.
