# Formal allocation 01 — STOP_OUTER_EXECUTION_TIMEOUT

Allocation: `live-scheduler-2254-r1-20260922-01`.

The exact publicly frozen source/hash/gates were verified locally before dispatch. Formal execution then exceeded the outer 120-second container-tool envelope before the runner wrote its all-at-once output file.

Observed retained facts:
- formal command started after zero source-hash mismatches;
- no `formal-01.json`, audit, or controls output was produced;
- therefore the completed scientific-case denominator is unknown and no policy/timing result is inferred;
- no same-ID retry, row replacement, pooling, threshold change, or result reconstruction is permitted;
- after the outer command was terminated, actor/watcher/runner processes were absent;
- one allocation-owned Xvfb process remained (`:90`) and was terminated by rescue cleanup; its socket was then absent;
- the temporary directory remained after rescue and is not treated as evidence of graceful cleanup.

Disposition: **STOP_OUTER_EXECUTION_TIMEOUT / HOLD_EVIDENCE_INCOMPLETE**.

This is an execution-envelope/harness retention failure under the existing #2254 question, not a new scientific Issue and not evidence that a scheduler policy passed or failed. Any continuation must use a new allocation identity and retain per-case checkpoints so a supervisor stop cannot erase the completed denominator. The frozen 8ms / 100ms / burst-3 / 50ms / 70ms science gates remain historical allocation-01 facts and are not retroactively changed.
