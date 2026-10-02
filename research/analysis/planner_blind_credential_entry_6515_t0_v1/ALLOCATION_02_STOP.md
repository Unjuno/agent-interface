# Allocation 02 stop record

Allocation `PLANNER-BLIND-CREDENTIAL-ENTRY-6515-T0-HOSTCPU-20261003-02` stopped before candidate invocation.

- Frozen base: `2ebde9d05592a3a8f866fafcb4cbef888f53d199`
- Newly observed `main`: `e7f11cdc2cdee42b0f745add6c4a93fc641abe6d`
- Candidate invocations: 0
- Auditor invocations: 0
- Formal outputs: absent
- Reason: `main` advanced after allocation freeze and before launch; frozen prelaunch gate failed.
- Disposition: `STOP_BASE_ADVANCED_BEFORE_RUN` (no semantic result; do not retry allocation 02).

`FREEZE_A02.json`, `PREREGISTRATION_A02.md`, and allocation 01 evidence remain immutable. A new allocation may use unchanged candidate bytes only with a new base pin, unique allocation ID and output path.
