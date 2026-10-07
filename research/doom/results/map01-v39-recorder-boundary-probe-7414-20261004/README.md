# PR #7414 recorder-boundary evidence rescue

This package preserves the distinct construction result added by the final
commit of PR #7414 without importing its stale source tree into current main.
PR #7414 is stacked on Draft PR #7386, whose base is Draft PR #7355; the full
branch is therefore not an independently mergeable main change.

## Results

- [`RECORDER_BOUNDARY_RESULT.md`](RECORDER_BOUNDARY_RESULT.md): synthetic
  incomplete-network-receipt test red on #7386 parent, green after the bounded
  failure-record repair; 13/13 candidate/auditor construction tests.
- [`MALFORMED_AUDIT_INPUT.md`](MALFORMED_AUDIT_INPUT.md): malformed hex input
  raised before the audit guard and returned explicit FAIL/HOLD after repair.
- [`SOURCE_PROVENANCE.md`](SOURCE_PROVENANCE.md): exact source commits, Git
  blob IDs, SHA-256 values, and original PR locations for source and outputs.

These are construction and adversarial-input results only. No live X11,
physical input/release, game, model, container, task effect, or formal
allocation is claimed. The consumed T0 STOP remains unchanged and was not
rerun. The documents here are an indexed rescue record; exact original raw
files remain available at the source commits identified in
`SOURCE_PROVENANCE.md`.
