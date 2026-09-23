# #3300 OrbStack asynchronous scorer construction probe v1

Decision: `PASS_CONSTRUCTION_PROBE_SCOPED`; original Issue #3300 remains `HOLD`.

## H/T/D/C/U

- H: call the exact current-main `_coherent_progress_sample` function against an advancing ViZDoom episode and retain each of its tic-read brackets plus the outer immediate-call spans.
- T: OrbStack Docker context; `vizdoom==1.2.3`; bundled `basic.cfg`/basic WAD; hidden `ASYNC_PLAYER`; ticrate 35; no game actions, model, network, desktop, or user input. Three conditions (idle, fixed local CPU work, 20 ms pre-call delay); 12 samples/condition; three consecutive calls to the unchanged scorer function/sample. The delay/load are construction controls, not frozen formal phase strata.
- D: retain `raw.jsonl`, exact scorer/runtime source hashes, image ID, raw SHA-256, and independently recompute each function decision from paired raw tic reads. Keep the earlier direct-read result and failed instrumentation attempt immutable.
- C: construction PASS only if all 36 rows have three outer calls, every inner read is paired/ordered, and each recorded scorer result matches an independent same-tic recomputation. No formal reliability inference.
- U: public bundled fixture only; phase offsets are not controlled or preregistered; no private MAP01 fixture or frozen all-three-failure allocation; no isolated production end-to-end scorer pipeline; no failure-probability estimate or gameplay/efficacy claim.

## Result

OrbStack image: `sha256:57ad79ade1fc4d961017fb46575af305b12dc552fa54ea9369c32733cc2017f9` (`linux/arm64`). Docker build succeeded; allocation ran with `--network none`. The initial instrumentation attempt stopped before a scientific row because the C++ getter is read-only; the proxy instrumentation rerun completed and is the only dataset below.

There are 36 rows / 108 outer scorer-function calls. Every outer call returned coherent after exactly one internal read pair; 108/108 paired tic brackets had equal before/after tic values across the three strata (each bracket consists of two getter reads). The independent audit is retained in `audit.py`; raw JSONL SHA-256: `bfa27da03e259af1c48da367cd688e301c932abf27263ce10345282a50d02b33`.

This shows the frozen predicate is callable in the pinned container and the read spans/decision can be retained without altering the production function. It does not test the originally proposed phase-offset distribution: the zero-offset labels here are load/delay conditions, not measured phase strata. Therefore this result does not satisfy #3300 and does not replace its `HOLD`.
