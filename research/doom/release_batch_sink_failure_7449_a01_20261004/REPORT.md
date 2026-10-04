# Historical per-row sink-failure audit — PR #7449

> **Status:** PR #7449 was closed without merge and superseded by the current-main V1 backend work in [PR #7635](https://github.com/Unjuno/agent-interface/pull/7635). This package freezes the earlier V3 implementation at `915c46d7f448003d82dd002d6e9fb34141e2712a`; it is historical evidence, not a finding about current main or the current PR. The V1 backend's position-by-position boundary matrix was separately retained in [PR #7644](https://github.com/Unjuno/agent-interface/pull/7644). A later ExecutorV13 BaseException gap is being tracked in [PR #7653](https://github.com/Unjuno/agent-interface/pull/7653); it is a distinct terminal-boundary issue.

## H/T/D/C/U

- **H:** PR #7449 head `915c46d7f448003d82dd002d6e9fb34141e2712a` preserves at-most-once publication attempts, but a sink exception on batch position 0 before acceptance leaves no emitted row carrying an explicit `delivery_unknown` disposition for that position.
- **T:** Run the exact upstream five-test fake-composition suite and a derived sixth test. The derived case injects a two-key release batch, makes the sink fail before accepting the first `input_release_transition`, and inspects the rows that the backend emits while finishing the incomplete batch. Compare with the existing accept-then-raise test. No real input, game, model, GUI, or container is used.
- **D:** The per-row disposition hypothesis is supported if the injected sink records the failing position as 0, while emitted rows contain no position 0 and only position 1 with `release_batch_disposition="publication_exception"`; acceptance uncertainty must not trigger a retry.
- **C:** This checks a deterministic fake sink around a synthetic owner. It does not prove the external sink's persistence semantics or how a full ExecutorV12 terminal is serialized.
- **U:** No X-server release, application receipt, physical dwell, task effect, live threat control, or MAP01 outcome is measured.

## Result

The upstream five-test suite passes. With one additional fail-before-accept fault case, all 11 tests pass. In that case the fake sink fails on `release_batch_position=0` before recording the row. The backend then emits only position 1, with `release_batch_size=2`, `release_batch_complete=false`, and `release_batch_disposition="publication_exception"`. The emitted output contains no per-row `delivery_unknown` record for position 0. The upstream accept-then-raise case remains at-most-once: the accepted position 0 is not duplicated and position 1 is emitted as incomplete.

This is a narrow per-row reporting gap, not evidence that physical release failed. The backend preserves later observed rows and does not retry a possibly accepted row; however, the failed row's delivery uncertainty is not represented in the row stream. The test harness does not include the outer executor terminal path, so it makes no claim about terminal-level diagnostics.

## Reproduction

From the repository root:

```powershell
python -m unittest discover -v -s research/doom/release_batch_sink_failure_7449_a01_20261004/source -p 'test_*.py'
```

`source/test_upstream_actual_composition.py` is byte-pinned to PR #7449. `source/test_sink_fail_before_accept.py` is a derived fault-injection copy that adds a sink failure before acceptance and asserts the missing position/disposition. The backend and v4 owner modules are exact snapshots from the same PR head.
