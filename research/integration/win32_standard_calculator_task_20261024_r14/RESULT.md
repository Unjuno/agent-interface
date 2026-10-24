# R14 result — prelaunch attempt-ID mismatch

## Disposition: PRELAUNCH_STOP

Before execution, the conditions file named `win32-standard-calculator-task-20261024-r14-7454b896`, while the frozen runner embedded `win32-standard-calculator-task-20261024-r14-4af3d08c`. The mismatch was caught by the preflight consistency check. The runner was never launched; there are no runtime receipts, and no observation or input occurred. The packet is preserved unchanged. `audit_r14.py` reproduces the ID and manifest check.
