# A12 limits and deviations

- Issue #59 remains unassigned with no live Doom lane, so this was limited to construction evidence.
- The planner transport is a recording fake. It accepts the exact `PersistentPlannerAdapter` input, but no model ran; useful interpretation and resulting behavior remain untested.
- The test uses synthetic typed HUD values, not OCR output or a running game. The monitor is evaluated on a single paired observation epoch and no pending model timing is reproduced.
- WSLc warned that swap-limit capabilities were unavailable (or cgroup was not mounted). The requested 512 MiB was limited without swap. A separate probe observed `cpu.max=100000 100000` and `memory.max=536870912`; no stronger resource claim is made.
