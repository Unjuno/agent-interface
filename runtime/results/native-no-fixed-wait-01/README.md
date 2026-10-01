# Fixed-wait omission intake
One primary-agent Calc trial on integrated main, seed 991291. Before starting,
the local plan fixed omission of the two explicit 250 ms post-action waits.
Text gaps remained 20/10 ms. No runtime defaults were changed.

The first action image showed only a partially painted format dialog; its
title was present but the buttons were not available for visual grounding.
The primary requested observation without input. After confirming the visible
format button, the next image still showed the dialog and save progress although
the recorded window list no longer listed the dialog. A second read-only
observation showed the finished sheet. Final independent XLSX readback matched
A1=779, A2=881. There were no repeated input actions.

The task succeeded but the local SDK client failed after finish: decision-6
(status) was published using non-atomic tee and was read before JSON was complete.
Client exit 1 is retained, not relabelled success. Owner PID was absent afterwards;
its exit code was not collected. Cleanup report covers tracked child processes
only, not all descendants. Future decision publication must use atomic rename.

Decision: do not promote zero post-action wait as a default. Retain explicit
waits and model-reviewed read-only continuation. This is one exploratory case,
not a matched performance test or a generic readiness detector. No sensor was
implemented. Raw files and hashes include the pre-run plan and transient images.
