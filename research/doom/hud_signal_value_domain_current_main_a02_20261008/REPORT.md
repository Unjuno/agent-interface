# MAP01 HUD signal-value admission — current-main A02

## H / T / D / C / U

**H — hypothesis.** Exact observed MAP01 HUD values outside the declared
health (1–200) and ammunition (0–999) integer domains can cross one or more
current-main source-refresh, action-contract, or snapshot boundaries. A
shared fail-closed domain check should reject them without changing UNKNOWN
handling or admitting a later favorable refresh frame.

**T — test.** Starting from current main `28b6f0fc0dd3cf6d798d97ee608a409ce773e409`,
added regressions before changing production code. The first run exercised
health 0/201, ammo -1/1000, booleans and floats at the relevant boundaries.
After the observed RED, added one immutable shared domain predicate and
validated refresh, action-contract, action-snapshot and typed-observation
snapshot admission. The shared predicate was exhaustively checked for every
integer from -1 through 1001 for both signals, as well as non-integers,
unknown signal names, and runtime table mutation. The 39 focused tests ran
under Windows Python 3.12 and Ubuntu WSL Python 3.12; changed modules also
passed WSL Python byte-compilation.

**D — disposition.** `PASS_REGRESSION_SCOPED`. Before the fix, 19 regression
subcases failed: 4 in source refresh, 3 in the action contract, 6 in the
reader-built action snapshot, and 6 in the typed-observation action snapshot.
After the fix, all 39 tests passed on both hosts, byte-compilation passed, and
`git diff --check` was clean. The source refresh refuses an invalid observed
value before submission and does not advance to a later positive frame.
Valid endpoints remain accepted.

**C — controls.** The added predicate is pure, bounded and has no I/O. It
requires `type(value) is int`, so Python booleans do not alias integers. The
MAP01-specific domains are explicit and immutable; this does not broaden the
generic interface signal schema. The test run used no model, game, GPU, GUI,
network, or live input.

**U — limits.** This checks numeric admission only. It does not establish HUD
glyph correctness within the numeric range, reader transfer to another WAD or
game, useful recovery, threat response, gameplay outcome, safety, or a live
#59 result. No WSLc container was started: the current #7924 record still
requires explicit release of the shared WSLc lane, and this pure CPU test does
not require a container boundary. The separate WSLc compatibility smoke,
Docker parity/cost, and memory-comparison questions remain open under their
existing Issues and are not resolved here.

## Reproduction

From `research/doom`:

```sh
python -m unittest test_doom_signal_value_domain_v1 test_source_refresh_v1 test_doom_action_validity_contract_v1 test_doom_action_snapshot_v1 test_doom_typed_observation_epoch_exact -v
```

The pre-fix TDD run exited 1 as expected. The post-fix command exited 0 with
39 tests. The identical command passed in Windows Python 3.12 and Ubuntu WSL
Python 3.12 (Pillow 10.2.0, NumPy 1.26.4).

## Provenance

This is an additive current-main successor to the numeric-boundary gap
identified in open PR #7596. That PR's branch is based on a much older main
and is not merged or rewritten here. Its earlier run and files remain intact.
This A02 covers additional current-main action-snapshot boundaries; it does
not rerun the old formal/game allocation or claim independent review. Merge
remains subject to current-main CI and nonauthor review.
