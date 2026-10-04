# #59 acknowledged scorer status separation — successor experiment

Status: PASS for the synthetic/local attribution contract only; STOP for any live or GUI qualification.

## H/T/D/C/U

- H — A scorer callback failure after a client update has returned must not erase or relabel the independently observed update acknowledgment.
- T — From frozen parent `603f7b70e66a3866c11684dc8c869f12479ce08d` (#7545 observed head), run the isolated V1 characterization and V2 unit suite with a fake game whose tic advances 2→11. No game, model, GUI, or controller allocation is used.
- D — Frozen parent ref: #7545 head `603f7b70e66a3866c11684dc8c869f12479ce08d`. The V1 characterization makes one update call, records `tic_after=11`, but emits `status=UPDATE_UNAVAILABLE` with no producer when the scorer callback raises. V2 tests: 4/4 PASS; V1 regression suite: 10/10 PASS; Python bytecode compilation and `git diff --check` PASS. V2 emits update ACK before invoking the sample callback and retains producer/update status on callback failure. A failed update has no producer and marks sampling `NOT_ATTEMPTED`. Simultaneous scorer and evidence-sink exceptions are both retained in a `BaseExceptionGroup`.
- C — This establishes event ordering and attribution under deterministic fakes only. It does not establish real-client behavior, timing/freshness, live Doom control, model/controller effect, GUI visibility, or integration with the canonical scorer sink. V2 is opt-in and changes the evidence event shape; do not substitute it into a live run without review and a separately allocated qualification.
- U — Next: independent code/evidence audit, CI on the isolated successor branch, review and integrate through PR if accepted. Revisit live qualification only after an authorized exclusive allocation and compatible container/runtime are confirmed. Docker on the current host was unavailable (`containerd` content blob open: `operation not supported`); no Docker rerun was attempted.

## Reproduction

From repository root:

```sh
PYTHONPATH=research/doom:research/doom/acknowledged_scorer_status_v2_59_20261004 \
  python research/doom/acknowledged_scorer_status_v2_59_20261004/test_acknowledged_scorer_status_v2.py -v
python -m py_compile \
  research/doom/acknowledged_scorer_status_v2_59_20261004/acknowledged_scorer_status_v2.py \
  research/doom/acknowledged_scorer_status_v2_59_20261004/test_acknowledged_scorer_status_v2.py
```

The test suite covers: ACK precedes scorer callback; callback failure preserves successful update status and producer identity without retry; update failure produces no false ACK and skips the scorer callback; simultaneous scorer and evidence-sink failures preserve both exceptions.

This is an additive successor experiment. V1 files and their recorded results are unchanged.
