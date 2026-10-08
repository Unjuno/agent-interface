# Issue #4148 preformal branch recovery status

This is a partial preservation of the public freeze/plan/construction record.
It is not an executable experiment bundle or a formal result.

- Original branch head: `e70821d846dbe0f8089ffd1eda34b01d3a2e97e3`.
- Its exact three files (`FREEZE.json`, `PLAN.md`, `PREFORMAL.md`) are copied
  unchanged. Formal allocation remains 0/26; no batch has started.
- `FREEZE.json` commits nine source/gate hashes, but the branch contains none
  of those nine source files, including `runner.py`, `audit.py`,
  `SCHEDULE.json`, and `EXPECTED.json`. No source archive is present. A
  bounded filename search under `/Users/taka/Documents/Codex/2026-09-19` and
  `/tmp` found no directory named for this allocation; that search is not
  proof of absence elsewhere.
- The Issue reports excluded construction outcomes (including 4/4 corrected
  construction checks), but their executable source/raw receipts are not in
  this branch. They are retained as Issue-reported history, not independently
  rerun or verified by this recovery.
- The frozen 26-case GUI allocation is untouched. No GUI/Xvfb, formal runner,
  Docker, model/provider, network, or user-desktop action was started.

The current outcome is `HOLD_SOURCE_BYTES_UNAVAILABLE`. This partial record
lets a future worker see the frozen gates and known construction boundary on
`main`; it does not make the allocation runnable. Issue #4148 remains open.
