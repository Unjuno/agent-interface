# Deviations and limits

- Issue #59 remains open and unassigned; therefore no new live game allocation was available. The experiment stayed at source-bound construction scope.
- The action contract's authored minimum and cover monitor's positive floor are separate current-main APIs. This result identifies their behavioral difference but does not establish policy intent or require code change without the live gate.
- WSLc warned that swap-limit capabilities were unsupported (or cgroup was not mounted); the requested 512 MiB was therefore limited without swap. The separate probe observed `cpu.max=100000 100000` and `memory.max=536870912`; no stronger resource-isolation claim is made.
- The initial independent audit produced HOLD due to an auditor-only end-of-output matcher bug. The hold is retained, and the corrected audit operates on the same frozen transcript and receipts without rerunning the experiment.
