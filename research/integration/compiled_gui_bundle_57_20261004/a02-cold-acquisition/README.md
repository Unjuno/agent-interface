# A02: cold acquisition + compiled GUI composition

Issue #57 integration construction check; no formal/live allocation. This advances A01's warm execution composition by connecting two caller acquisition stages to the compiled GUI graph and checking per-attempt accounting, typed abstention and failure missingness.

The runner has three cases: a cold two-model-stage positive path into two guarded compiled transitions; a coarse-stage `no_match` that stops before target selection or execution; and a failed upstream model attempt with unavailable token usage but known image count/wait. It was run against current main caller SHA `8517d130d7336b27e6ddfc0ee06629d2b1183070cf845c3ef4ada8adc3cd79ca` and the PR #7330 head `ed326ccfeae1c66fde4ec38d0d3dcd9b54ca53d0`, candidate caller SHA `e9be73955d849a8d627450752a4b6b97a410cdd08e9424746d954e23015a654d`. Both runs use compiled runtime SHA `d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014`.

Reproduce with Python 3 from the matching checkout:

```sh
PYTHONPATH=research/live_control:. python3 -B research/integration/compiled_gui_bundle_57_20261004/a02-cold-acquisition/run.py /tmp/RUN.json
```

`RUN-MAIN.json` and `RUN-PR7330.json` are the raw adapter-ledger/compiled receipts. `audit.py` is saved-output-only and verifies the source identities, task outcomes, transition count, attempt order, usage aggregation, missing usage, image/wait metadata and no-target/no-execute boundary. The retained `AUDIT.json` passes.

Results: both positive arms count two model attempts (input 200, cached subset 50, output 20, reasoning subset 6, two visible images, 20 ms synthetic wait) and then report two compiled transitions with outer effect success. Cached input is retained as a subset and not added to input. Both no-match arms make one completed coarse-model call and stop with no selected target, compiled invocation or outer effect check. Both failed-model arms report one attempted/zero completed calls, retain `usage=null`, one visible image and 12 ms synthetic wait, and perform no execution.

Scope: fixed test doubles and synthetic accounting values, no schema preflight, target-handle mint, live GUI, provider or physical input. The millisecond-like waits are fixtures, not observed performance; token counts are fixtures, not provider usage. This establishes contract composition only, not real cold cost or efficiency.
