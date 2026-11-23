# Current-main WSLc optimized release 3 s diagnostic R07

Status: **DIAGNOSTIC CLEANUP OBSERVED / TASK FAILED / PRODUCT HOLD**.

A single optimized WSLc run with in-memory diagnostic budgets XRes=1.0 s and retired-release=3.0 s completed the unittest with exit 0. Owner disconnect was independently observed after 199.66 ms; the release worker completed in 1,188.39 ms and read A/B up. A separate parent keymap readback was neutral. This is physical release evidence for this synthetic fixture, while the public cancellation envelope remained `release_confirmed=false`, task success false, and terminal `runtime_failed`.

The independent old-task oracle failed: the effect count increased from 1 to 25 and a late A press was observed. All keys were up at the late horizon. A fresh generation completed exactly one independently scored task without old-generation input after the new session began, while the old fence remained UNKNOWN. Thus the larger diagnostic budgets let the control path reach verified release, but they do not make the old operation's task safe or successful. No source was changed, and this single altered-bound diagnostic is not evidence to widen either production timeout.