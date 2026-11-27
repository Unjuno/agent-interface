# R03 disposition

The frozen R03 Edge run completed one actual headless-browser Submit action.
The caller returned `TASK_SUCCEEDED`; one local HTTP POST carried exactly
`value=t991025-1`; the compiled receipt reports one completed transition with
verified release; both screenshots, OCR text/state, caller usage ledgers,
receipt, POST body, and cleanup record were retained. Edge and its private
profile exited/cleaned successfully. Source and capture hashes match.

The independent auditor returned `HOLD` because it required exact-token OCR
on every observation. The pre-action OCR was exact (`t991025-1 Save`); the
post-submit page no longer contained the form and OCR returned empty/unknown.
That final observation is scored by the compiled method's
`submission_pixels_changed` predicate, not by the field-value predicate. No
failure is changed to a pass and no gate is relaxed after observing the data.

The task-effect/control observations are preserved, but R03 is not a passing
packet under its frozen rule. A prospective R04 changes the predeclared rule
to require exact OCR before Submit and a changed submission page after Submit,
then repeats once with a fresh task token. No target-generation, two-action,
provider, economics, recovery, MAP01, or runtime-readiness claim follows.
