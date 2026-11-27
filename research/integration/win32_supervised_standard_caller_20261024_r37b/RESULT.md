# R37b — bounded recovery followed by fresh-generation task success

**Disposition: `PASS_SCOPED` for one paired native-Windows sequence.** The
frozen R36 strict release audit passed 10/10. The additive R37b audit passed
11/11, including a separately observed task effect after phase 1 completed.
This is one paired sample, not a reliability estimate.

The run used CPython 3.11.9 on the user-authorized Windows 10 host, with source
commit `5c907bb27f30b055180d3b9cdf7a4b706b1ff34f`. WSLc and Docker were not
used. The first R37 packet stopped in input-free preflight because of an
incorrect repository-root path. That `FAIL_OR_UNKNOWN` setup record is retained
in sibling packet [R37](../win32_supervised_standard_caller_20261024_r37/preflight.json);
it sent no native input. R37b repaired the path, froze a new attempt ID and task
token, and passed all 11 preflight checks before the live sequence.

Phase 1 used one fixture, one observation, one validated program, one dispatch
and one public cancel. A same-generation independent readback confirmed Q-down
before cancellation, and the exact call remained `running`. The cancel response
took 2.039 ms. The held Q-up callback stayed open for 1,250.649 ms after that
response while the standard caller made 77 exact-call result polls. Recovery's
Q-up `SendInput` returned 626.382 ms after cancel; the independent same-
generation sampler observed Q-up in 57 samples before the held callback
returned. Its 601-sample process exited cleanly, and a final separate readback
was neutral. The producer and fixture exited, and the original foreground
window was restored.

Two boundaries remain explicit. The hook did not record a second distinct
Q-up callback. Also, `interface_close` returned `closed` with
`release_confirmed=false`, although the terminal cancellation receipt,
independent samples and final readback confirmed neutral state. The fixture's
click/save effect occurred before cancellation; phase-1 `task_success` stayed
null.

Phase 2 began only after phase 1 passed its strict gate and its resources were
closed. It used a second fixture process and a distinct target generation. One
public observation bound that generation through validation and dispatch. The
dispatch returned `pending`; five read-only lookups retrieved the same call as
`completed`, with terminal release confirmed and a neutral completion readback
containing independent state-query witnesses. The server-side oracle then
matched the exact click/save/token effect and returned `verified` with
`task_success=true`; its receipt matched the new call ID, operation ID, target
generation and oracle ID. The effect oracle observed success 14,157 ms after
phase 2 started. That timestamp is the oracle read time, not an exact physical
application-effect timestamp. The second fixture exited and foreground
restoration passed. Its `interface_close` also reported `release_confirmed=false`
despite the completed action's separate neutral release evidence.

The raw inputs, MCP responses, exact-call polls, hook trace, same-generation
state series, oracle evidence, phase timing, preflight, conditions and audits
are preserved here. No phase was replayed or retried.

This does not establish broad reliability, MAP01, matched efficiency,
real-application transfer, WSLc GUI behavior, kernel causality, or a hard
real-time guarantee beyond the frozen finite windows. The fresh-generation task
is a separate session/task after bounded recovery, not continuation of the old
unknown call.
