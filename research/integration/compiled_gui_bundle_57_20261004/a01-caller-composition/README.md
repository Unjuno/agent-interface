# A01: caller v3 + compiled GUI test-double composition

Issue: [#57](https://github.com/Unjuno/agent-interface/issues/57). This is a local construction/integration test, not a live or formal efficiency allocation.

The runner invokes the compiled GUI runtime through the shared adaptive caller's warm-reuse execute adapter. It tests three cases: positive two-action completion, changed/unknown intermediate state, and a completed compiled action sequence followed by unavailable outer task-effect verification. Both arms use the same compiled-runtime blob (`d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014`). Caller source blobs are exact and recorded in each raw result.

- Main source was checked out at `bfaa12181f81cac133747ca8a1b7eb277aa64424`; caller SHA-256 `8517d130d7336b27e6ddfc0ee06629d2b1183070cf845c3ef4ada8adc3cd79ca`.
- The candidate source was PR #7330 branch `fix/caller-current-main-composition-i76`, commit `ed326ccfeae1c66fde4ec38d0d3dcd9b54ca53d0`; caller SHA-256 `e9be73955d849a8d627450752a4b6b97a410cdd08e9424746d954e23015a654d`.
- At later main checks `8d9940c4e0afe7895715bce77fa9f7e455e06cad`, `96f7041fe6b3eb71127ac4eca0ed31d313c29ad2` and `2f72c6474167f93a2e1a6e2b8a497a1a8a6d266a`, both caller and compiled-runtime file hashes were unchanged from the tested main source.

Reproduce from either checkout using Python 3:

```sh
PYTHONPATH=research/live_control:. python3 -B research/integration/compiled_gui_bundle_57_20261004/a01-caller-composition/run.py /tmp/RUN.json
python3 -B research/integration/compiled_gui_bundle_57_20261004/a01-caller-composition/audit.py
```

For the audit command, place `RUN-MAIN.json` and `RUN-PR7330.json` beside the auditor under the expected names. The committed audit binds both raw JSON files, runner and auditor source hashes, then checks the three expected state transitions/outcomes. It independently checks both zero attempted calls and an empty attempt ledger for all three warm routes. `audit-coverage-test.py` independently corrupts each arm's `warm_changed` and `outer_effect_unavailable` accounting rows and confirms the saved auditor rejects them.

Observed: the positive arm completes two compiled transitions on both sources. The changed arm stops after one transition with `unknown_state`, preserving one completed action on both sources. When the outer effect verifier returns unavailable, both sources report `TASK_NOT_VERIFIED` and confirmed delivery; main drops `execution_progress`, while the PR #7330 candidate preserves `{"status":"completed"}`. All three warm routes make zero model attempts by design.

Scope: test-double observations, admissions, action receipts and effects only; no GUI, physical input, model calls, cold acquisition, image accounting, real warm reuse, task-distribution sampling, or efficiency estimate. Result is diagnostic evidence for the composed interface and caller custody contract only.
