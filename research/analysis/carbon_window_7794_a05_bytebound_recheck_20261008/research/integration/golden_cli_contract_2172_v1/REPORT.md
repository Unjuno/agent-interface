# Golden desktop v3 → unified CLI contract audit (#2172)

## Result

**PASS_DESKTOP_VERTICAL_SLICE_CONTRACT_AUDIT_SCOPED**

This additive static audit maps 11 required lifecycle states across the frozen main sources without changing runtime, golden evidence, or generated indexes:

- setup/launcher and v3 doctor;
- model attempt and observation/accounting;
- freshness-bound guarded dispatch;
- refusal/invalid request;
- useful exact effect;
- stale-target invalidation;
- repair;
- terminal release;
- cleanup failure.

Every row has an explicit source-backed field/token mapping, no row grants authority, and no state is left unmapped. Partial effects remain representable through the dispatch result and retained task/effect fields; task success is represented separately from program completion through `exact_submission`, `independent_evaluation`, and release fields.

Frozen source identities:
- `runtime/golden-demo-v3.sh`: `ef489bbd68e3f80fac060b179fe90da2cce8d209`
- `runtime/golden_desktop_demo_v3.py`: `26db03b8400b03fbe5272bd4ae5ad9c3a82d31a2`
- `runtime/golden_desktop_demo_v2.py`: `cf777186879fc3d550194aa9cbc8a7239ca991ff`
- `runtime/cli_v1/api.py`: `5674bd39e3cb2170095f476dac90e2a781f4f77a`
- `runtime/cli_v1/README.md`: `8cafa39718f0d5d66cb73adeb3aa99f0f1cce6d6`
- `runtime/GOLDEN_DESKTOP_DEMO_V3.md`: `940213efdcb582d6c7399d0cd1f0afc3fecb1c4a`

Audit digest: `24861e56716ff2d3cae941d8b49b3e7b0d65e069a00e10d94601cc236ecbcb9a`.

## Boundary

This is a source-contract audit only: model=0, GUI=0, network=0, input=0. It does not implement the adapter, run the desktop route, prove GUI correctness, model utility, latency, token savings, or task completion. A fresh successor is required for adapter implementation and integrated acceptance.
