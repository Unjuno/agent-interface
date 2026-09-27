# Successor #2156: persisted-token crash-liveness pre-model boundary

## H/T/D/C/U

- **H**: Separating durable token existence, token delivery, and external effect status prevents blind replay after a persistence-before-return crash.
- **T**: Six frozen crash/effect cases: visible token, lost token, pre-persist crash, corrupt journal, effect already applied, and effect unknown.
- **D**: Standard-library deterministic policy/oracle; no model, GUI, network, runtime, user input, or real action-owner.
- **C**: Journal alone never proves external effect; corrupt evidence reconciles; non-idempotent ambiguity queries/aborts rather than blindly replaying; fresh identity is only for pre-persist absence.
- **U**: Model recovery quality, held-out process boundary, real action-owner effects, concurrency, power loss, latency, and liveness transfer remain unmeasured.

## Disposition

`HOLD_PRE_MODEL_CRASH_LIVENESS_POLICY`: 6/6 oracle agreement, blind non-idempotent replays 0, new authority 0, external effects 0, model invocations 0. This is not crash-liveness or model evidence.
