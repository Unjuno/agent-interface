# Release-ledger sink-mutation current-main regression — Issue #59 A02

## H / T / D / C / U

**H.** A sink callback that mutates a release row's `release_batch_position` to
an unrelated value before raising must not corrupt the release-delivery ledger.
This is checked at both complete-batch publication and incomplete-cleanup
publication, with the failed row at the first, middle, and last position and
with both fail-before-accept and accept-then-raise behavior.

**T.** Tested repository snapshot: main commit
`81a59aed13492ba1d52ea80e03d48c3d8de7b2c5`. The pre-existing backend binds
each row object to its ledger position in `context["delivery_rows"]`; this
successor adds regression coverage without changing production code.
Historical predecessor evidence remains immutable in
[closed PR #7669](https://github.com/Unjuno/agent-interface/pull/7669), whose
frozen #7635 parent was `12522ccd0b58d3333da1d241d1b04f2c888c46e6`.

**D.** The two new methods cover 12 mutation cases: 6 complete publication and
6 incomplete cleanup. All 12 pass on the tested main snapshot. The complete
`test_release_backend_v3_actual_composition` module passes 14/14. Historical
A01 remains a valid fail/pass result only for its frozen source; A02 shows the
later main implementation passes the same matrix using identity-bound ledger
positions.

**C.** Deterministic in-process backend composition with synthetic owners and
sinks. The callback mutation is injected by the test harness. Docker image
inspection stopped before launch because the local containerd image-list
operation returned `operation not supported`; the A02 run therefore used the
local Python runtime. The predecessor's Windows and WSLc records are retained
in #7669 and are not presented as A02 container results.

**U.** This does not show that a production sink mutates rows, and does not
establish physical release, X-server behavior, application consumption,
recovery efficacy, useful feedback, or MAP01 completion.

## Reproduction

From the repository root:

```sh
python3 -B -m unittest research.doom.test_release_backend_v3_actual_composition -v
```

The two new test methods each exercise positions 0/1/2 and both sink-acceptance
modes. See `RESULT.json` and `VALIDATION.txt` for the frozen snapshot and
observed scope.
