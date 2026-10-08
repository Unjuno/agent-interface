# Golden desktop v3 emitted-result provenance audit

Decision: **HOLD_SOURCE_EMISSION_GAP**

Pinned main sources:
- `runtime/golden-demo-v3.sh` blob `ef489bbd68e3f80fac060b179fe90da2cce8d209`;
- `runtime/golden_desktop_demo_v3.py` blob `26db03b8400b03fbe5272bd4ae5ad9c3a82d31a2`;
- `runtime/golden_desktop_demo_v2.py` blob `cf777186879fc3d550194aa9cbc8a7239ca991ff`.

The v3 launcher is only a delegating shell wrapper. v3 imports v2, replaces the doctor, and delegates `run_live` to v2. The emitted live report is therefore the v2 `golden-report.json` object with schema `agent_interface_golden_desktop_live_v2`; v3 adds no machine-readable result boundary.

## Field provenance

Doctor checks and environment are emitted by the v2 run. Model-call usage, image counts, release flags, repair, independent evaluation, and task rows are emitted by v2's report construction. However, the source audit finds no v3-specific emitted fields or independent v3 result writer for the frozen nine-state integration schema. The v3 doctor schema is `agent_interface_golden_doctor_v2`, not the golden-v3-result schema.

No source-backed evidence was found in this audit that makes task success an independently emitted semantic result distinct from the v2 `passed` aggregate, nor that exposes a v3 cleanup-failure result boundary. A report wrapper or prose cannot be promoted to those fields.

## Scope

No runtime, model, GUI, network, input, or Docker invocation. This is a source-first integration blocker. Earlier schema/adapter evidence remains unchanged; a future successor must add or identify a real emitted boundary before adapter implementation.
