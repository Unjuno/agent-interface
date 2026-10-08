# Issue #6380 T0 — retained FAIL_METHOD / no retry

Allocation `issue6380-constraint-elicitation-t0-20261002-01` ran its single frozen candidate command successfully (32 rows; candidate SHA-256 `4e4c545a7fc16e9dcb0dec78d22ebc38d89aa08aec8846a641f379639d8a3eb9`). Its single independent auditor invocation exited 1 at `audit_t0.py:46`:

```text
assert r["hidden_constraint_credit"] is should_credit
AssertionError
```

The cause is a candidate construction mismatch: `GENERIC` returns status `ANSWERED` with the scripted hidden clause value, but the contract builder adds clauses only for `CONFIRMED_FORBIDDEN`. The generic response therefore records no hidden clause, while the frozen auditor expects the scripted generic clarification to retain the respondent-confirmed clause. This invalidates the policy comparison; no method PASS or comparative efficacy claim is supported.

The preregistered candidate cap (1) and independent auditor cap (1) are consumed. No source patch, candidate replay, audit replay, or replacement case is authorized under this allocation. The original frozen source, pre-run hashes, `candidate.json`, and failed auditor traceback are preserved. Disposition: `FAIL_METHOD_CONSTRUCTION_MISMATCH`; not an infrastructure STOP. Any future successor would be a separately frozen allocation and must not rewrite this record.
