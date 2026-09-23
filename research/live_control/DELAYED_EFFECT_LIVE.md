# Model-driven live wait across a delayed effect

The fixed delayed-effect comparison showed that prior execution evidence should
change the next decision from submit to wait. This episode tests that strict path
in one newly running Chromium session rather than replaying an archived image.

The assistant-side driver sent exact token `t000243` and Return once through the
shared Linux/X11 runtime. The fetch-based fixture kept the same form visible and
delayed its saved artifact for five seconds. The first explicit checkpoint was
UNKNOWN. Its strict v3 view included the completed five-step program, prior steps,
empty verified release, expected request/contract binding and unknown application
effect. That view and the current screenshot were sent to one Luna/low call.

The model returned `wait_and_check` with a requested 1,000 ms delay. The outer
model call took 6.494 seconds, so no additional sleep remained. The caller issued
one new read-only effect checkpoint immediately after the model returned. It was
VERIFIED, the saved value was exact, and final independent evaluation succeeded.
No GUI input was admitted after the UNKNOWN checkpoint. If the model had proposed
`submit_once` or `verify`, the driver would have refused before GUI input.

| Quantity | Observed value |
| --- | ---: |
| Model calls | 1 |
| Input / output / reasoning tokens | 9,770 / 74 / 28 |
| Model runner | 6.494 s |
| Additional scheduled wait | 0 s |
| Input acceptance to post-action image ready | 598.805 ms |
| Input acceptance to UNKNOWN | 667.934 ms |
| Input acceptance to VERIFIED | 7,257.393 ms |
| Post-UNKNOWN input admissions | 0 |

The model computation overlapped enough of the declared application delay that
the caller needed no separate sleep. This is not proof that model inference makes
arbitrary waits free: the model itself remained slower than the five-second
fixture delay, and this is one authored task. The result supports doing semantic
reasoning concurrently with external application progress, then using a cheap
effect query instead of blocking first or repeating input.

Artifacts are under `results/delayed-effect-live-01/`. The audit verifies pinned
sources, all raw model events and arrivals, exact prompt/evidence/image binding,
the single task Return, UNKNOWN then VERIFIED ordering, absence of post-UNKNOWN
input, saved bytes, exact frame reconstruction, release and cleanup.
