# MotorState focus freshness / TOCTOU successor

Allocation: `motor-state-freshness-toctou-20260923-01`.
Lineage: closed #27; merged #4194/#4207; pointer-effect successor #4219 is separate.

## H
A MotorState snapshot that matched the intended Calc focus when captured can become wrong before task input. A fixed maximum snapshot age catches sufficiently old evidence but cannot detect a focus transfer that occurs inside the age budget. Re-observing the current X-server focus immediately before first task input should fail closed on both fast and slow focus changes while preserving the stable Calc effect.

## T
Provided Linux execution container, LibreOffice Calc 25.2.3.2, Xvfb, Python-Xlib/XTEST, openpyxl. Controller task input is XTEST only. UNO reads Calc A1 after the controller returns and is evaluator-only. A separate Tk root is an explicit wrong-surface sink and logs received key-release characters.

Factorial directed matrix: three scenarios × three policies × two repetitions = 18 fresh private X-server/Calc lifetimes.

Scenarios:
- `stable`: no focus transfer; decision age must remain <250 ms.
- `change_within_250ms`: snapshot is taken while Calc focus matches, then X11 focus is transferred to the helper; decision age must remain <250 ms.
- `change_after_250ms`: same transfer followed by an added 280 ms wait; decision age must exceed250 ms.

Policies:
- `snapshot_only`: act from the matching snapshot with no age/current check.
- `age_guard`: act only if the matching snapshot age <=250 ms.
- `jit_reobserve`: read current X-server focus immediately before task input and refuse on mismatch. The current observation supersedes the old snapshot age.

Each case first exposes a held Shift key through XTEST and independently observes held then neutral release. If policy decides ACT it sends `7` + Return. Stable ACT must produce Calc A1=`7`. Wrong-surface ACT must leave Calc blank and the helper must receive `7`.

Formal: six immutable 3-case batches: rep0 stable/within/after, then rep1 stable/within/after. One invocation per batch, no retry/replacement/pooling/post-result tuning. Separate construction history is excluded.

## D
`PASS_MOTOR_STATE_FRESHNESS_TOCTOU_SCOPED` requires all18 first cases complete; held/release/final-neutral18/18; authority none18/18; stable correct effect6/6; snapshot-only wrong-surface effects4/4 under both focus-change scenarios; age-guard wrong-surface effects2/2 for within-budget changes; age-guard stale refusals2/2 after-budget; JIT mismatch refusals4/4 with task input0 and wrong-surface effects0; within decision ages <250ms and after ages >250ms; independent raw audit errors=[] and >=10 coherent evidence corruptions rejected.

Any JIT wrong-surface input/effect is FAIL. If the frozen timing cells do not fall on the intended sides of250ms, the result is HOLD timing-discriminator-not-exposed, not threshold tuning. Missing process/effect/raw evidence is STOP/HOLD.

## C
The 250ms value is a diagnostic boundary, not a recommended production TTL. The X11 focus transfer is directed, and the naive comparators are deliberately weak. Just-in-time observation can still race with a change after its read; this experiment only narrows the check/use gap, it does not prove atomic input admission. Refusal trades liveness for correctness.

## U
One Calc/X11 action, one synthetic wrong-surface helper and two directed timing regions. X-server focus is not physical HID telemetry. No natural focus-change rate, model/planner usefulness, screenshot/token/latency benefit, atomic check/use guarantee, cross-platform reliability, runtime promotion or product claim.

## Variable table

| field | meaning | SI unit | frozen definition |
|---|---|---|---|
| `snapshot_ns` | MotorState snapshot time | s stored ns | `time.monotonic_ns()` immediately after initial focus read |
| `decision_age_ns` | snapshot-to-decision age | s stored ns | decision time minus snapshot time |
| `MAX_AGE_NS` | diagnostic age boundary | s stored ns | exactly 250,000,000 ns |
| `snapshot_focus` | initial observed X focus XID | 1 | X server input focus at snapshot |
| `jit_focus` | current focus before input | 1 | only for JIT policy |
| `N` | formal cases | 1 | 3 scenarios ×3 policies ×2 reps =18 |

Dimensional check: timestamps and age are time; XIDs/counts are dimensionless and are never added to time.
