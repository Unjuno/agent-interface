# PR #9315 supersession receipt r02

Captured 2026-10-21 20:52 UTC against current main
`410eb938bfb1f3cd4658e3136dded5d14eabd7c3` and exact PR head
`76626da8b03df25024d12efb5f1dde2f12c53ed2`. GitHub reports the PR OPEN/DRAFT,
based on `9bf7ec15ea78eccd752adee1af8d00dc9545eaa0`. This receipt updates the
custody review after PRs #9320–#9332; it does not rewrite prior run outcomes.

## Exact-tree reconciliation

Compared the complete file trees at `origin/main` and the PR head. The trees
differ at 181 paths. Every path present in the PR head also exists in current
main; 112 additional paths exist on main from later work. Of 69 paths present
in both trees with changed bytes, 49 become identical after line-ending
normalization and 20 have substantive current-main content:

- Current entry points and design records (`docs/CURRENT_GOAL.md`,
  `docs/IDEAS_AND_OUTCOMES.md`, `docs/INTEGRATION_PLAN.md`,
  `docs/REPOSITORY_CLEANUP_PLAN.md`, `docs/REPOSITORY_CONSOLIDATION.md`,
  `docs/WORKER_WORK_MAP.md`, `docs/architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md`,
  `docs/ideas/safety-control-agenda.md`, and the r119 idea-coverage record) have
  later reconciled state on main.
- The supervisor spec is retained on main as historical/superseded text. Its
  body matches the PR version byte-for-byte (SHA-256
  `ff8bcff4489afdb25ac09581c56d15c00d2d3e9108cf608343478a4f07919582`). The
  research index, packet README, and packet manifest point to the successor
  records.
- The six runtime paths are superseded by the current implementation and its
  later caller/bystander fixes. The PR version of
  `runtime/guarded_x11_v1/cancel_supervisor.py` removes `supervisor_pid` binding
  and accepts unrelated resource-base reuse. Do not merge it. Current main
  retains that identity check and the refusal tests in
  `runtime/guarded_x11_v1/test_cancel_supervisor.py`; local verification passed
  11/11 with `python -m unittest runtime.guarded_x11_v1.test_cancel_supervisor`.

The r01, r02 and r03 XRes diagnostic manifests each verify all entries against
current main (10/10, 10/10 and 15/15; 35/35 total). This includes the log files
previously reported absent from the PR head and the r03 runner, whose current
main bytes match its manifest. PR #9321 separately records transfer and
verification of the supervisor evidence packet at integration time. No
experiment was rerun, no result was promoted, and no unique PR path needs a
new copy.

## Disposition

Close PR #9315 as superseded by #9320/#9321 and reconciled by #9322/#9323,
#9326, #9331 and #9332. Do not merge its stale runtime or restore its older
entry-point snapshots. Preserve its branch and immutable historical packet.
Issues #17 and #57 remain open for the unresolved computer-control research.

The next cleanup batch is one bounded idea-family disposition from the current
semantic-route queue, with its live Issue, related PRs, canonical record and
first outcomes refreshed before any state change.
