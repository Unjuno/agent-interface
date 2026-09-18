# #1227 formal execution stop

Decision: **STOPPED_OUTER_EXECUTION_TIMEOUT_NO_RESULT**. Scientific disposition: **NONE**.

The already-frozen `TEMPORAL-SPECULATION-VALIDITY-ANCHOR-X11-TRANSFER-20260918-001` formal runner was invoked exactly once with no source, threshold, fixture, or schedule change. The outer execution boundary reached 60 seconds before the detached run serialized either `RESULT.json` or `EXIT.txt`. `STDOUT.json` and `STDERR.txt` are both zero bytes. A post-stop process check found no remaining runner, fixture, or Xvfb process.

All eight frozen scientific files still match their preregistered SHA-256 values after the stop. Formal invocation count is 1; reruns/replacements/tuning are 0. This is therefore not a scientific failure and none of the intended 24-pair endpoint claims are made.

A legitimate continuation must use a **fresh successor allocation** that changes only the execution/serialization envelope (for example immutable smaller batches with immediate per-batch serialization) while holding #1227 science, 24-pair schedule, 120 ms duration, source/evidence anchor definitions, negative controls, and decision thresholds fixed. The stopped invocation is pooled 0.
