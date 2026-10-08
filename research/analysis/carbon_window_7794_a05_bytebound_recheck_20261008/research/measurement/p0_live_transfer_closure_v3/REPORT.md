# Result — #1282 P0 live-transfer closure

Decision: **PASS_P0_ONLY_LIVE_CAUSAL_EFFECT_REMAINS_SCOPED**.

- #1100 parent current-DAG closure retained exactly.
- #1276 live physical-edge transfer is promoted only to `LIVE_PHYSICAL_EDGE_TRANSFER = PROVEN_LIVE_SCOPED`.
- `LIVE_CAUSAL_EFFECT_SAMPLE = UNPROVEN_CURRENT`.
- same-process live useful-control proven: false.
- cross-process live useful-control proven: false; a measured clock axis remains required.
- primary invocation1 / reruns0.
- independent audit errors[].
- source Git objects rehash exact3/3 plus roadmap.
- copied-result overclaim mutations for same-process and cross-process useful-control were rejected.
- RESULT SHA-256: `5a1ae9df5d6dd0565ef0ac95a7efaf7a83ce456bbac20e1581940e4490e77519`.
- AUDIT SHA-256: `0a14097980c4f84f3e7ab9e0b9e1da0a335716a412dbe57c43718a30d17caf70`.

Interpretation: after #1276, P0 no longer needs another physical-edge implementation or transfer experiment. The only remaining same-process live evidence gate is an exact-lineage physical actuation bound to an independently scored application effect on a valid comparable clock. #1276 Tk press/release callbacks remain control-regression witnesses, not task-usefulness evidence.
