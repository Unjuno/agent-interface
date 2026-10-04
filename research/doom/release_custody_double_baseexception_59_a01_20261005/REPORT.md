# Double-BaseException release-custody audit — PR #7635

## H/T/D/C/U

- **H:** At PR #7635 head `636f61941e3da887a1641e4399c2f0e3373a7974`, the executor preserves custody from a worker `BaseException` when final cleanup succeeds, and terminalizes a cleanup `BaseException`. If both steps produce custody-bearing interruptions, the cleanup ledger may replace the worker ledger even though the worker exception is the one ultimately propagated.
- **T:** Load the exact pinned ExecutorV13 source. Inject `KeyboardInterrupt` with ledger A from `execute()`, then another `KeyboardInterrupt` with ledger B from `release_all()`. Inspect propagated exception identity, terminal error, and terminal custody.
- **D:** Supported if the worker exception is re-raised but the sole `release_batch_delivery` field contains only cleanup ledger B, omitting ledger A. Falsified if terminal preserves both custody records or a documented invariant excludes this double-fault combination.
- **C:** The real backend may not produce both failures in one execution; this harness establishes a control-flow/data-retention loss under the constructed case, not its frequency or operational impact.
- **U:** Stub imports/parent class and direct method invocation; no thread scheduling, real sink, input device, GUI, game, model, or live allocation.

## Result

The exact head re-raises the original worker `KeyboardInterrupt` carrying ledger A. It emits one failed terminal, but `terminal.error` names the cleanup `KeyboardInterrupt` and `terminal.release.release_batch_delivery` contains only ledger B. The earlier worker custody is absent from the terminal. The focused test passes by asserting this observed behavior.

## Reproduction

From the repository root:

```powershell
python -m unittest discover -v -s research/doom/release_custody_double_baseexception_59_a01_20261005/source -p 'test_*.py'
```

The frozen source is exact PR #7635 blob `fb49db4336de46d9d36783cd8f12738664243b36` at head `636f61941e3da887a1641e4399c2f0e3373a7974`.
