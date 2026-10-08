# Release-all BaseException custody A01

## Frozen question

Issue #59's release-batch telemetry must not leave ExecutorV13 without a terminal when cleanup publication raises a process-level exception. This construction check isolates a `KeyboardInterrupt` raised by `backend.release_all()` after the program step succeeds. The exception carries one per-position `unknown` release receipt.

## Result

The baseline at `61e5e877101f3182f64986406a5552917d554446` emitted no terminal and retained the active intent after the worker exception. The candidate at `636f61941e3da887a1641e4399c2f0e3373a7974` emitted one `failed` terminal with `release.verified=false` and the exact `release_batch_delivery` custody, cleared the active intent, and then propagated the same `KeyboardInterrupt` through the worker hook. The independent auditor checks both raw outcomes and source/dependency pins.

Reproduce with:

```powershell
python research/doom/results/release_all_baseexception_59_20261005/run.py
python research/doom/results/release_all_baseexception_59_20261005/audit.py
```

The baseline/candidate commits and shared dependency hashes are recorded in `raw.json`; the exact runner and fixture are in `run.py`. This ran on Windows CPU with no WSLc (not installed), container, Docker, game, model, GUI, OS input, or live allocation. It does not prove physical release, durable sink persistence, task effect, or MAP01 completion.
