# Construction host run 02 — audit hardening successor

Status: `PASS_T1_SCOPED` for deterministic host construction only. This run
supersedes the weaker mutation-check coverage in construction-host-03 without
altering that earlier result. No formal Docker/OrbStack execution is claimed.

- Frozen GitHub main: `6b1ad36c0628098c2d1c28b0a1b371db099aecce`.
- Host: macOS 26.6.2 arm64; CPython 3.14.5; standard library only.
- Runner invocation: exactly 1; 32 deterministic rows.
- Independent audit invocation: exactly 1; raw-only, no simulator import.
- Audit: `PASS_T1_SCOPED`, zero errors. In addition to all 32 decision/oracle
  checks, corruption controls now prove detection of abort-status, action-role
  provenance mismatch, and generation mismatch.
- The raw data is deterministic and byte-identical to the earlier host runs;
  the audit implementation is the corrected source. Attempts 01–04 remain
  append-only prior records, including the auditor's failed construction checks.
- Syntax check: `python3 -m py_compile simulate.py audit.py`, passed.
- Container invocation count: 0. Formal run awaits exact #5085 owner/allocation,
  current-main and exclusive-window assignment.

## SHA-256

| Artifact | SHA-256 |
|---|---|
| `PLAN.md` | `319868f04def8f5499cb8cc73333af4fc40766323efe657dae92043bd3e9aae7` |
| `simulate.py` | `7f7cbc4564345c8f1721d51e9e229d2d3a71d0229d6f1116882532d6209963ea` |
| `audit.py` | `5b9634f934e2bab18d2ac0387e0779d04f0d98efe475c4aa22ef2ff3565f5d6d` |
| `raw.json` | `76af071d682818315d469edf808d45745b4225db758ac889ca18f8e8da225908` |
| `audit.json` | `6d3fbef7ef4b08a66c6ec97269cc12e53d3f5ad43635849c3a6110178968e452` |

This is a finite synthetic-history result, not a production transaction-manager,
distributed-commit, or GUI/task-effect claim.
