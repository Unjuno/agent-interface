# Exact-head cleanup BaseException audit — PR #7635

## H/T/D/C/U

- **H:** At PR #7635 head `61e5e877101f3182f64986406a5552917d554446`, an exception carrying release-batch custody from `backend.release_all()` bypasses ExecutorV13 terminal publication because the cleanup handler catches `Exception`, not `BaseException`.
- **T:** Load the exact pinned `executor_v13.py` blob. Call `_run_with_watcher_cleanup()` with an empty step list, a minimal lease whose interruption state is empty, and a fake backend whose `release_all()` raises `KeyboardInterrupt` with `release_batch_publication`.
- **D:** The finding is reproduced if that exception escapes and no terminal event carries failed status or custody. It is falsified if cleanup emits a terminal with the custody ledger before preserving/re-raising the process-level exception.
- **C:** This is a deterministic direct executor-method construction. Dependency imports and parent class are stubbed; it does not test thread scheduling, backend implementation, sink persistence, or OS input.
- **U:** No physical release, GUI/application effect, game, model, live allocation, or task outcome is measured.

## Result

The exact-head harness passes its assertion: `KeyboardInterrupt('cleanup sink interrupt')` escapes with the `delivery_unknown` payload attached, while zero terminal events are emitted. The issue is distinct from the step-loop BaseException path that #7635 fixed in this head.

## Reproduction

From the package directory, run:

```powershell
python -m unittest discover -v -s source -p 'test_*.py'
```

The frozen source is the exact PR #7635 blob `4cd9efe0f6c0a2ddb098ff8b066e0155d04fa6b8` from head `61e5e877101f3182f64986406a5552917d554446`.
