# Mindustry repeat/reset contract v1 — retained first outcome

Task: `MINDUSTRY-REPEAT-RESET-CONTRACT-20260917-001`  
Issue: #863  
Immutable source BASE: `b9dcc5cc456b95ed97d36276ec5557bcae1cad5d`

Disposition: **`PASS_MINDUSTRY_REPEAT_RESET_CONTRACT_SCOPED`**.

The source-first frozen disposable-container formal runner was invoked exactly once; formal reruns were zero. The independent auditor passed with no errors, and four structured corruption controls were all rejected. No provider/model call, GUI, Mindustry process, X11 input, network task action, or user-data action occurred.

## What the contract establishes

The existing retained one-tile Mindustry scorer is applied **before** every benchmark reset. Six frozen tasks run in exact order `A1/A2/A3/B1/B2/B3`, representing the intended future `A/A/A/B/B/B` comparison shape. Every task effect independently scores `VERIFIED` before reset.

After each score, a separate reset verifier requires the benchmark state to return to the exact canonical task state: target empty, full guard projection restored, source/core/copper restored, paused/alive with no pending plans, and a strictly increasing benchmark epoch. All six reset witnesses pass.

The controller-visible projection contains only `task_id`, task text, layout, and benchmark epoch. Engine tiles, copper, source/core state, unit state, oracle/evaluation fields, and `contract_satisfied` are not exposed.

## Frozen negative controls

- missing reset -> next-task authority remains false;
- target still occupied after reset -> rejected;
- non-target guard mutation after reset -> rejected;
- copper not restored -> rejected;
- wrong task rotation -> the existing scorer contradicts the task even though a later reset could restore canonical state;
- duplicate/non-monotonic reset epoch -> rejected;
- explicit oracle-field leak -> rejected.

This prevents benchmark reset from laundering a failed agent task into success.

## Integrity

- formal invocation: 1; reruns: 0;
- source-first freeze commit: `dbcddd35033a5ad545b19db7d9b02977efd23774`;
- retained scorer Git blob: `9e9b17117ed020dc11dd42283d8d22b935f10cdf`;
- retained plan Git blob: `d3330f157cf8acd2950e2ffa56a8801687603f80`;
- RESULT SHA-256: `5d2e0b1696876c0baacdeb5563a6a863e97e18a36624638f644ae999fd81ddf6`;
- AUDIT SHA-256: `ff2aec832da933bc254b57e4826de4f0208d119e406ca09764615549b0188a9e`;
- CORRUPTION SHA-256: `f20e1b049a0fc366997065c3af7cecb15fe05a8c76c12a2b259b73052db16364`.

## Interpretation / boundary

This closes a benchmark-design blocker for the future #57 Mindustry second-domain allocation: the same semantic one-tile task can be repeated without adding a new world-target detector, while preserving per-task independent scoring and keeping benchmark reset outside agent effects.

It does **not** prove that the live Mindustry fixture can perform this reset correctly, that layout A→B mutation safely invalidates persistent references, or that plain/current-optimized/persistent arms save provider tokens or wall time. A live fixture implementation and the final matched allocation remain separately authorized work. The next useful pre-live step is to source-close the minimal fixture reset/mutation implementation; do not add a new perception mechanism unless that integration exposes a concrete need.
