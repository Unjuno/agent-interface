# T0 v2 result — source event-kind gate

Disposition: **PASS_CONSTRUCTION_T0_SYNTHETIC_CONTRACT_ONLY**

- Intake main: `b0190453a787102189429e4b8c32032cf60efd17`.
- Revision: adds a fail-closed requirement that source `event_kind == TASK_EFFECT`; unsupported scorer kinds remain HOLD. The v1 first outcome and raw are preserved unchanged.
- Construction tests: 11/11 passed on CPython 3.12.10.
- Synthetic runner: 14 rows; includes unsupported source event-kind.
- Independent raw-only audit: separate Python subprocess; 14/14 re-derived; errors=0.
- Corruption controls: 7/7 rejected.
- Raw SHA-256: `3b89697c62a4c427a34c0c737f99ecd203c3122796126e6b34e4791063122373`.
- Audit SHA-256: `8b9a5542e87dc37e7a1bdbc43fd14091aac05eec74839716acfdb798d29d9981`.

Scope: deterministic synthetic contract only. No Docker, game, model, GUI, input, or live allocation. No task-effect reproduction, recovery benefit, safety, MAP01 clear, latency, causal or human-tempo claim. #4193 predecessor HOLD remains immutable.
