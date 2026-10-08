# V39 context + measured-release composition A01

## H — hypothesis

On a conflict-free synthetic union of current `main` plus PR #7602 (typed
state/per-key edge projection), PR #7750 (owner-issued per-admission identity),
and PR #7769 (per-key cancellation cleanup brackets), the three focused test
suites can execute together and retain their scoped contracts without source
conflict or test regression.

## T — test

Use the exact source heads and merge-tree recorded in `FREEZE.json`. In a
temporary export of the composed source, run exactly:

```powershell
$env:PYTHONPATH = "$PWD/research/doom;$PWD/research/live_control"
py -3.11 -m unittest research.doom.test_map01_v39_typed_state_feedback -v
py -3.11 -m unittest discover -s research/live_control/owner_keyup_admission_id_5156_a03_20261005 -p 'test_*.py' -v
py -3.11 -m unittest discover -s research/doom/map01_v39_perkey_bridge_a01 -p 'test_*.py' -v
```

Run each suite once after the source and decision rule are frozen. This is an
offline source-composition construction test; it does not use an X server,
game, model, OS input, shared container, GPU, or live allocation.

## D — decision

`PASS_COMPOSITION_SCOPED` requires all three Git merges to be conflict-free,
the final composed tree to match the frozen tree OID, and every focused suite
to exit zero with all tests passing. Any conflict or test failure is retained
as `FAIL_COMPOSITION` if source/test behavior is responsible, or
`HOLD_CONSTRUCTION` if the test environment or runner is defective. No source
or threshold repair is permitted within this frozen attempt.

## C — competing explanations

Clean Git merges and separate component passes may still conceal runtime-order,
threading, real X11, application-consumption, scorer-independence, or event
correlation failures. These suites may only exercise fake owners and
source-level state. The independent-useful-feedback and bounded-recovery
questions remain outside this construction test.

## U — uncertainty and scope

The source union is an integration candidate formed from open PR heads; none is
thereby approved, merged, or authorized for live use. The test cannot establish
real X server edge timing, ViZDoom behavior, threat response, useful feedback
during planner latency, recovery efficacy, matched effectiveness, safety, or
MAP01 completion. The separately assigned live #59 allocation remains the
gate for those claims.
