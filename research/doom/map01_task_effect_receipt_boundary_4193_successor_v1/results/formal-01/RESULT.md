# T0 result — task-effect receipt boundary

Disposition: **PASS_CONSTRUCTION_T0_SYNTHETIC_CONTRACT_ONLY**

- Source freeze: current main `b0190453a787102189429e4b8c32032cf60efd17`; source Git blobs recorded in FREEZE.json.
- Runtime: CPython 3.12.10, local host. No Docker container or shared resource lease.
- Construction suite: 10/10 passed.
- Synthetic runner: 13 fixed rows across unique positive, missing/wrong identity, incomparable/early clock, duplicate, NO_INPUT positive, unsupported effect, missing release edge and non-neutral terminal.
- Independent auditor: separate Python subprocess, no import of the runner or candidate classifier; 13/13 independently derived; errors=0.
- Corruption controls: 7/7 rejected (case deletion, verdict mutation, wrong plan, authority escalation, time mutation, unsupported effect-kind mutation, physical-edge mutation).
- Raw SHA-256: `69cfdc1ec3d00e86f0ccaa365d4b95aa752a48b874397cc0eaf6423f36508ba2`.
- Audit SHA-256: `82f697950f94ffd8a3eaf0e9095b2ad5a2a00a6e9aff7df4e4b6d90ee3f7f3e2`.

## Limits and next gate

This only validates a deterministic synthetic evidence contract. It provides no live physical occupancy, task-effect reproduction, bounded recovery efficacy, survival, MAP01 exit, latency, causal attribution or human-tempo evidence. The predecessor #4193 remains HOLD and immutable. No formal Doom/model/GUI/input execution occurred. A matched bounded-recovery versus control live allocation remains necessary and requires a separately frozen policy/source plan plus an exact coordinator resource assignment before any formal invocation.
