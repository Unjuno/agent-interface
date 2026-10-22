# Deviations and limits

- Current guidance requires a new conflict-free live-game lane before the threat-exposure gate. Issue #59 is open and unassigned, so this experiment stayed construction-only and did not launch Doom or spend a live allocation.
- The main worktree available for source extraction has numerous unrelated dirty files; the controller and guard inputs were taken directly from its Git object database at the frozen main commit. No tracked checkout files were edited.
- WSLc warned that swap-limit capabilities were unsupported (or the cgroup was not mounted). The requested 512 MiB was therefore limited without swap. The separate probe observed `cpu.max=100000 100000` and `memory.max=536870912`; no broader enforcement claim is made.
- The monitor's ammo guard floor is one. This does not test propagation of a larger planner-authored ammo minimum, nor whether the cancellation loop reacts in time under live conditions.
