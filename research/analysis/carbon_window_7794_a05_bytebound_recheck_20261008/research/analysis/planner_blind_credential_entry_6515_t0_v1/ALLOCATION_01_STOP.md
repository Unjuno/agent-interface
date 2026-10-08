# Allocation 01 stop record

Allocation `PLANNER-BLIND-CREDENTIAL-ENTRY-6515-T0-HOSTCPU-20261003-01` was stopped before candidate invocation.

- Frozen base: `c33380b3b08792a331ee11f7aee05e3d41437e3e`
- Newly observed `main`: `2ebde9d05592a3a8f866fafcb4cbef888f53d199`
- Candidate invocations: 0
- Auditor invocations: 0
- Formal outputs: absent
- Reason: base advanced after allocation freeze and before launch; frozen prelaunch gate failed.
- Disposition: `STOP_BASE_ADVANCED_BEFORE_RUN` (no semantic result; do not retry allocation 01).

The original preregistration and freeze remain unchanged. A distinct allocation may use the same candidate bytes only after creating its own freeze against the then-current base and a unique output path.
