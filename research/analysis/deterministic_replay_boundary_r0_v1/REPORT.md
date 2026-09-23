# #1748 Deterministic replay boundary sufficiency

Decision: **PASS_DETERMINISTIC_REPLAY_BOUNDARY_SUFFICIENCY_SCOPED**

## Result

A deterministic runtime was modeled with ten external event variants:

- OBS(0/1)
- MODEL(0/1)
- TOOL(0/1)
- AUTH_OPEN
- AUTH_CLOSE
- TICK
- REQUEST

The retained record contains the initial-state identity plus a strictly monotone sequence index, event type and typed payload for every external boundary event.

Across every event sequence of length 0 through 5:

- sequences checked: **111,111**
- exact replay mismatches: **0**
- record sequence-integrity errors: **0**

For every source sequence of length at most 4, every prefix cut and every one-event alternate suffix were also checked:

- fork replay checks: **543,210**
- fork replay mismatches: **0**

Thus, within the frozen deterministic model, replaying the complete ordered boundary record reproduces the exact runtime trace, and a recorded prefix can be forked by applying a different later event with the same result as direct execution of that prefix plus event.

## Why the recorded fields matter

Each deliberately incomplete record representation has signatures shared by executions with different observable results:

| Missing information | Ambiguous signatures |
|---|---:|
| total event order | 1,406 |
| MODEL payload | 28,981 |
| authority open/close events | 4,681 |
| CLOCK/TICK events | 7,381 |
| TOOL payload | 28,981 |

Simple witnesses are retained in RESULT.json. Examples include OBS(0),OBS(1) versus OBS(1),OBS(0) for missing order; MODEL(0) versus MODEL(1) for missing model payload; and the empty history versus AUTH_OPEN when authority events are omitted.

These are non-identifiability results: the same incomplete record can correspond to different state/output traces, so no deterministic replay algorithm can recover the original execution from that incomplete record in general.

## Corruption controls

Four malformed complete records are rejected:

- duplicate/out-of-order sequence number;
- invalid payload;
- unknown event type;
- wrong initial-state identity.

All four controls pass.

## Integrity

- formal invocations: **1**
- reruns: **0**
- replacements: **0**
- tuning after freeze: **0**
- independent audit errors: **[]**
- result digest: `9a53fd3104c3820b6e27ffe3564b50c785d2a1bf31dafe8262695805e8a8644d`
- audit digest: `d6d15dda4e1a91b3bdb314b6fce37eda2e50ff04371074c52237415a63d939a8`
- frozen PLAN/prove/audit SHA-256 values remain exact after formal execution
- GitHub RESULT/AUDIT Git blobs match the exact local formal output bytes

## Interpretation

This establishes a **sufficiency contract for a deterministic reducer**, not a complete production recorder.

A practical Agent Interface recorder must first identify every external or nondeterministic boundary that can change runtime behavior. If OS scheduling, random identifiers, external processes, filesystem/network state, hidden clocks, model/tool responses or unordered delivery affect execution but are not recorded, this theorem does not apply.

Likewise, total ordering is sufficient here but may be unnecessarily strong. Independent commuting events may admit a more compact partial-order trace; that is a separate optimization question.

The next empirical rung should replay an already-retained deterministic experiment from recorded boundary data without re-invoking its external dependency, then deliberately remove one boundary class to verify the predicted divergence.

No GUI/model replay, storage-efficiency, latency, token, human-tempo or production-runtime claim follows from this result.
