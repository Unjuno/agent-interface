# #1451 retained requested-Astra frontier-gap eligibility — first outcome

Decision: **PASS_RETAINED_FRONTIER_GAP_ELIGIBLE_SCOPED**

Execution contract: source-first container analysis, formal analysis invocation **1/1**, reruns **0**, replacements **0**, tuning **0**, independent audit invocation **1/1**. No model/provider/network/GUI/X11/task-input/shared-runtime action.

## Frozen provenance

- Repository: `Unjuno/agent-interface`
- Intake commit: `4f03b7a8ee80a2601a68ebd976d135f2db306ca4`
- Exact retained files: `research/live_control/results/timing-envelope-openttd-l-{02..11}/fixed-astra-control/model-1-stdout.txt`
- 10/10 raw files are preserved in `FROZEN_RECORDS.json` with exact Git blob SHA-1 and raw bytes.
- 10/10 parse successfully, `exit_code == 0`, `requested_model == "gpt-6-astra"`, `requested_effort == "medium"`.
- `observed_model_identity == null` in 10/10 and `cost == null` in 10/10.

## Frozen comparison constants

- Controlled T1 useful-reaction deadline: **12.000000 ms**.
- Retained T1 max ACTIVATE useful-effect latency: **2.692318 ms**.

## Retained model-process intervals

`stdin_closed_ns -> exited_ns` per run:

| run | interval (ms) |
|---|---:|
| 02 | 12,275.2935 |
| 03 | 15,337.2268 |
| 04 | 14,330.1069 |
| 05 | 13,914.1879 |
| 06 | 9,989.1436 |
| 07 | 11,866.0255 |
| 08 | 11,964.6512 |
| 09 | 15,088.7397 |
| 10 | 15,521.6686 |
| 11 | 10,392.4882 |

Summary, using the preregistered type-7 p95 convention:

| interval | min (ms) | median (ms) | p95 (ms) | max (ms) |
|---|---:|---:|---:|---:|
| `stdin_closed -> exit` | 9,989.1436 | 13,094.7407 | 15,438.66979 | 15,521.6686 |
| `started -> exit` | 10,428.0873 | 13,222.5624 | 15,802.07583 | 15,974.4855 |

Ratio to frozen T1 max useful-effect latency 2.692318 ms:

| interval | min | median | p95 | max |
|---|---:|---:|---:|---:|
| `stdin_closed -> exit` | 3710.239132x | 4863.742210x | 5734.341111x | 5765.169122x |
| `started -> exit` | 3873.274739x | 4911.218660x | 5869.319980x | 5933.357612x |

The smallest strict retained interval is **9,989.1436 ms**, which is greater than the frozen **12 ms** deadline in all 10/10 records. The retained T1 max effect latency **2.692318 ms** remains below 12 ms.

## Integrity

Independent audit: **AUDIT_PASS**. It independently decodes the frozen raw bytes, recomputes Git blob SHA-1, reparses every JSON record, recomputes primitive intervals, summary statistics, exact rational ratios, and the disposition.

Artifact SHA-256:
- `FROZEN_RECORDS.json`: `ff8d2c298ff8e450c5f9d1d4b8735c99205f41909408bff30c057d371d33b7a8`
- `analyze.py`: `9a05af0e22d07e56fa75c3fa96aec4dbbc86305805ea05152f2edc1df30b89fa`
- `audit.py`: `3d68c33e0e5e7b92f5aeb2eaa02a42b7952a1945229eb84b2053084f8c7d4ac5`
- `RESULT.json`: `d6eebc48175c9860a086dbcb41bebf0c9669bcc1b9406e5cb76636410be8b702`
- `AUDIT.json`: `e98486e710fdc37a9ef0e1e494ecbfae292e00ad7d62f3fe8c2003d057e07978`

## Scope / next rung

This establishes only that these ten **historical requested-Astra route / real model subprocess** traces contain a retained open interval far longer than the controlled T1 deadline. It does **not** independently verify served-model identity, provider first-token timing, future-call latency, semantic answer quality, or real T2 end-to-end concurrency.

Per #1451, this PASS only makes a separately preregistered real-frontier T2 allocation eligible. It is not itself T2 success.
