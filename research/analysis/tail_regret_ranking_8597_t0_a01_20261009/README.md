# Issue #8597 T0 A01 — tail-regret ranking sensitivity

A deterministic finite synthetic test of whether a predeclared upper-tail summary can expose a route-ranking difference hidden by equal mean opportunity regret. The retained result is `PASS_METHOD_SCOPED` for this fixture only.

- `PROTOCOL.md`: frozen H/T/D/C/U, estimand, exact contrasts, and stop rules.
- `FREEZE.json`: current-main anchor, semantic references, and SHA-256 values for frozen inputs and code.
- `candidate.py`, `visible.json`: visible finite route/action fixture and candidate output logic.
- `truth.json`: audit-only target states and categorical controls.
- `candidate_raw.json`, `audit.json`: one formal candidate result and one independent raw-only audit.
- `REPORT.md`, `RUN_RECORD.md`: result, commands, custody, and scope limits.
- `SHA256SUMS.txt`: package integrity manifest.

Reproduction after source freeze:

```sh
python3 -B candidate.py --dir .
python3 -B audit.py --dir .
```

Do not rerun the formal commands for this consumed allocation. Construction test commands are listed in `CONSTRUCTION.md`.
