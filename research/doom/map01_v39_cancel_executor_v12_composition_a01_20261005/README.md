# V39 V13 cancellation receipt × current ExecutorV12 composition A01

This additive experiment asks whether the candidate V13 per-key cancellation cleanup receipts coexist with the current-main ExecutorV12 aggregate release-publication barrier. It is distinct from C12's V12 explicit-key-up/cancel-during-sync case and from the PR #7805 ExecutorV3-only test.

Read `PROTOCOL.md` and `SOURCE_LOCK.json` for H/T/D/C/U and frozen source identity. OrbStack stopped before container startup; the exact failure and fallback scope are in `ORBSTACK_STOP.txt`. Three runner setup attempts are retained as STOPs (formal_01 through formal_03); formal_04 is the sole completed candidate run. The independent audit reports `PASS_EXECUTOR_V12_COMPOSITION_SCOPED`.

Reproduce the local fallback from the repository root with:

```sh
python3 -B -m py_compile research/doom/map01_v39_cancel_executor_v12_composition_a01_20261005/run_candidate.py
python3 -B research/doom/map01_v39_cancel_executor_v12_composition_a01_20261005/run_candidate.py
python3 -B research/doom/map01_v39_cancel_executor_v12_composition_a01_20261005/audit.py
```

The candidate runner refuses to overwrite formal_04. Historical STOPs are not candidate retries and their paths remain immutable. Full local CI checks are listed in `COMMANDS.txt`.
