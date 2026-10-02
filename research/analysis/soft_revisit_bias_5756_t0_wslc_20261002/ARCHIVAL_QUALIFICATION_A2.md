# Allocation-02 preparation archive qualification

Issue: [#6442](https://github.com/Unjuno/agent-interface/issues/6442),
successor to [#5756](https://github.com/Unjuno/agent-interface/issues/5756).
Original branch: `research/soft-revisit-bias-5756-t0c-20261002`.
Original tip: `55ff24a41b4511f4f109862dfc066ed5fb76260a`.
Allocation: `SOFT-REVISIT-BIAS-5756-T0-20261002-02`.

This is an archive of the exact allocation-02 preparation source, not a
candidate result. The original `FREEZE_A2.json`, `SHA256SUMS_A2`, policy,
fixtures, runners and tests are retained unchanged. All 11 files covered by
the original A2 source manifest verified locally; the 13 focused policy and
auditor-contract tests also pass on host Python. These checks are construction
evidence only and do not consume the frozen WSLc construction invocation.

## H/T/D/C/U

- **H — Hypothesis:** a bounded soft revisit bias may recover targets behind
  incompletely inspected or visibly revised branches better than hard
  visited-branch exclusion, without extra revisits on stable-complete controls.
  The authored development simulation already ties soft with stateless on the
  partial/revised stratum (16/16 each); no soft-specific advantage is
  established.
- **T — Treatment:** the preserved freeze specifies 32 synthetic fixtures ×
  four policies (128 policy/fixture rows), with a 12-event limit and a pinned,
  offline WSLc runtime. This archive did not invoke WSLc, candidate or auditor.
- **D — Decision:** `STOP_SHARED_WSLc_OWNER_ACTIVE` / preparation HOLD; no
  scientific verdict. Candidate=0, auditor=0, allocation-02 WSLc
  construction=0, retries=0. The frozen base is
  `f4fcea6a67f1d8695626447d97ae697fa454a04e`, not current main, so it cannot
  be used as a current formal start freeze.
- **C — Controls:** host-side manifest verification was 11/11 and the focused
  contract suite was 13/13. These do not demonstrate the specified WSLc
  runtime, shared-host exclusivity, or scientific outcome.
- **U — Uncertainty:** Issue #6442 records an active parallel owner on the
  same WSLc host and requires explicit release plus a fresh main/source/image/
  output check. No release is inferred from an idle container list or this
  archive. The fixtures are authored synthetic graphs; no GUI/model/task
  effect or general search benefit follows.

The original branch also deletes unrelated MAP01 construction-log files and
reverts shared documentation/index snapshots. Those deletions are deliberately
not carried into this recovery. The predecessor allocation-01 STOP and its
raw gate evidence remain untouched.
