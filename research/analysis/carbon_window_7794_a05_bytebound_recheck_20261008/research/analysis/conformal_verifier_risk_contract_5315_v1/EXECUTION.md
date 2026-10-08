# Execution record — Issue #5315 allocation 01

| Stage | Container/command | Exit | Outcome |
|---|---|---:|---|
| Construction tests | Host CPython 3.14.5; pinned OrbStack CPython 3.12.14 | 0 / 0 | 4/4 each |
| Formal | Frozen `COMMANDS.md`, pinned image, no network | 0 | 20,000 rows; raw SHA-256 `4ead9d0a552db86332a4c8ac08b9f6e01fcc1f6066e645ae15ead9c9395c8b37` |
| Audit 01 | Frozen `audit.py`, separate process | 1 | `FAIL_AUDIT`; row/aggregate/oracle checks passed, its changed-outcome mutation control was a no-op. Preserved at `results/formal-01/audit.json`. |
| Audit 02 | Frozen successor `audit_v2.py`, separate process; same raw and receipt | 0 | `PASS_FIRST_UNIT_SCOPED`; 20,000 rows, exact aggregate reconstruction, all finite-sample gates and 3/3 mutation controls passed. |

Formal allocation count: one. Formal reruns/replacements/exclusions/tuning: zero. Audit-v2 is an additive auditor-only successor, not a simulator rerun. Full result and limitations: [REPORT.md](REPORT.md).
