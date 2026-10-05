# A06 STOP — auditor launcher unavailable

Status: `STOP_AUDITOR_NOT_STARTED_LAUNCHER_UNAVAILABLE`.

The frozen protocol specified exactly one fixture-generation, candidate, and auditor invocation, with no retries after freeze. Fixture generation completed once (80,000 rows; exit 0) and the candidate completed once (exit 0). The single auditor launch attempt used `py -3 auditor.py ...`; PowerShell reported that `py` was not recognized. The auditor process therefore did not start, produced no auditor result, and no scientific disposition is available. This is an execution STOP, not a method failure or finding about the frozen hypothesis.

The candidate output and observed-count fixture were copied into the auditor working directory as the prescribed handoff. That directory contained only `auditor.py`, `candidate.raw.json`, `observed_counts.json`, and `SCORING.json`. Because the frozen allocation prohibits retry, no alternate launcher or rerun was attempted. The retained command error is `results/auditor-launch-error.txt`; candidate and fixture outputs remain intact.

Scope remains synthetic and method-only. No participant, GUI, model, GPU, network, WSLc, Docker, or external data was used. A future attempt requires a distinct successor allocation with a verified interpreter executable frozen before execution.
