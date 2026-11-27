# Result: target-query isolation leaves three synchronous cleanup blockers

Base main `6ca6adc51618d02765afd2de97b25a96dadffe95` includes #8939.
The actual Python bridge, observation/alias handling, additional input guard,
scoped cancellation and public dispatch/session/backend are exercised. Only X
transport/platform setup and the selected read-only target reader are Fake X.
The fixture stubs preflight and backend focus; this does not qualify real focus,
physical input, an application effect or a complete task.

| Cell | While named gate is closed | After gate resumes |
|---|---|---|
| Healthy | No artificial gate | CTRL+a completes, verified fake-neutral cleanup |
| Capture × cancel/expiry | CTRL held; no result or release receipt; query worker idle | Failed execution, CTRL released, no a press |
| Observation persistence × cancel/expiry | Same held prefix and missing result | Same refusal and cleanup |
| Trusted callback × cancel/expiry | Same held prefix and missing result | Same refusal and cleanup |

Cancellation calls the actual bridge method with the active context token. Its
acknowledgment explicitly says release is unconfirmed; the fake clock remains
before the original deadline. Expiry cells instead advance that clock exactly
to the original deadline without cancellation. No measured wall-time bound is
claimed. The harness releases every gate; eventual cleanup after that release
does not prove finite recovery from an indefinitely blocked dependency.

Normal and optimized Python each complete the frozen seven-cell construction.
Each saved-raw audit passes 70 checks and rejects four mutations: erased held
state, false early return, a following task key press and false release status.
Each bridge directory retains its actual images, observations, mint, guard,
program, public dispatch and result artifacts. `FILES.json` pins every output
file; raw summaries pin `SOURCE_FREEZE.json`, which includes collector/auditor,
plan, runtime sources and dependency versions. Source postchecks pass.

The first normal construction failed before bridge creation with an existing
output-directory error. `construction-first-failure/` retains its original
collector and freeze plus failure description and empty partial directory. The
repair uses a fresh bridge child directory; successful collections use fresh
`normal-v2/` and `optimized-v2/` paths. This is a harness repair, not an omitted
failed experimental cell or a new live allocation. No initial outcome was erased.

Decision: retain #8939 as named query isolation. Full observation/control-plane
separation is still false for guarded Python programs using additional input
guards. A reader-only connection cannot safely host the existing capture routine
unchanged: it mixes observation acquisition, artifact retention, source/history
publication and trusted callback work. The next implementation must separate an
immutable acquired-frame reply from input-owner association/admission, keep one
input writer, reject late source/generation/deadline replies and keep persistence
and callbacks out of cleanup's dependency path. Do not move the input connection
onto a concurrent capture thread or remove the visual guard to make this pass.

No runtime change is made here. #17 remains open, as do physical transport stalls,
independent release verification, task effect, bounded recovery and matched
efficiency. This construction consumes zero real GUI/container/model allocations.

Recheck saved results without executing the collector:

```powershell
python -B -m research.live_control.guarded_sync_boundaries_20261015.audit research/live_control/guarded_sync_boundaries_20261015/normal-v2 --output <fresh-audit.json>
```

The collector intentionally refuses changed source or existing output paths.
Retain these frozen outcomes when current runtime later changes.
