# Formal execution STOP — Issue #5550 T0

**Disposition: `STOP_ALLOCATION_WINDOW_EXPIRED`.** This append-only record supersedes the `PASS_T0_SYNTHETIC_SCOPE` formal disposition in `REPORT.md` for allocation `MAXPERM-SUPERVISOR-5550-T0-ORBSTACK-20260930-02`. The predecessor report, freeze, source, raw candidate output, and audit output remain unchanged for auditability.

## Observed evidence

- The bounded execution window recorded in `FREEZE.json` and coordination Issue #5085 was `2026-09-30T16:25:00Z/2026-09-30T16:40:00Z`.
- Host filesystem timestamps for both `raw/formal-01.json` and `raw/audit-01.json` are `2026-10-01T01:49:17+09:00` (`2026-09-30T16:49:17Z`). The shell opens the redirected output before launching Docker, so each invocation began after the recorded window ended.
- Both Docker commands exited 0; raw SHA-256 remains `f17273be18b33083353a883c47c2834a3c33457cb4daada2227aeaf00bd6eb8b`; audit SHA-256 remains `594e785a1a607c7bdab636e3687201fc225d0e0075ca0eec1be6423db60aad2d`.
- A post-run `docker ps` showed `concentration-aware-ns:checker` and `cans-cusp-spatial-compile` active. These containers were not inspected or altered; temporal/resource overlap with this run cannot be excluded.

## Interpretation and handling

The retained finite-DFA output is exploratory evidence only. The audit's internal consistency and exit status do not repair the expired-window/resource-exclusivity failure. No accepted formal PASS, FAIL, or UNCERTAIN disposition is assigned to Issue #5550 from this allocation; the formal hypothesis remains unresolved. The prior 7/7 local construction tests remain construction-only.

This allocation is consumed and released. No candidate or auditor retry is permitted under this allocation. A successor formal test requires a fresh current-main/source freeze and an explicitly granted, non-overlapping resource window before any container invocation. This stop record makes no claim about the scientific truth of the earlier modeled counts.
