# Current-main recovery status — 2026-10-01

This recovery preserves the original #4369 source, plan, freeze and test
artifacts, and ports only the three string-before-membership guards to the
current `main` contract. It is not a rerun or reproduction of the retained
140-case allocation.

## Source reconciliation

- Recovery base: `e9742ae867addd1b78fac65fa48650b52bee3b97`.
- Current-main contract blob before this port:
  `d889c83e532abcb5cf80db25063d8215dbde9ee9`.
- The old e9q4 branch is based on `4a1f3957e91b412a64769199f78f2c4b0102d28b`.
- Its candidate contract omits `WINDOW_ACTIVATE` support that current main
  retains. That unrelated omission is deliberately not carried into this port.
- The port changes only the `pointer_move.frame`, `pointer_button.button`, and
  `observe.frame` membership checks. The focused regression test is preserved
  unchanged from the old branch.

## Evidence boundary

Issue #4369 reports `PASS_PROGRAM_ENUM_TYPE_COMPATIBILITY` for one frozen
140-case comparison, with a 3,587-check raw audit and 10/10 effective
corruption controls. The old branch does not contain that raw result/audit
payload. Therefore this recovery treats the matrix outcome as issue-reported,
not independently verified from committed bytes. PR #4381's merged packaging
cross-check is distinct evidence and is not substituted for that allocation.

No formal/matrix rerun is authorized or performed by this recovery. The code
port is gated separately by focused local regression tests and current-head CI;
neither those tests nor CI will promote the missing 140-case raw evidence.
On macOS arm64 / CPython 3.14.5, the focused enum regression module plus the
existing core contract and platform-probe modules passed **36/36**. This is
host-local unit evidence, not the frozen Linux/CPython 3.13.5 matrix, Docker/
OrbStack validation, or reproduction of the reported raw audit. Issue #4369
remains open for the evidence-delivery disposition.
