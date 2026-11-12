# C01-A02 commands and first outcomes

A01 (setup STOP; do not rerun):

```powershell
py -3.11 -B research/live_control/results/v13-v4-explicit-up-composition-c01-20261004/run.py
```

Observed exit code 1: `ModuleNotFoundError: No module named 'lease'` during import, before candidate wrapper logic. Transcript and disposition: `PREVIOUS-STOP-A01/`.

A02 candidate (executed once, exit code 0):

```powershell
py -3.11 -B research/live_control/results/v13-v4-explicit-up-composition-c01-20261004/run.py
```

Saved raw: `RAW.json`.

Saved-output audit (separate, read-only):

```powershell
py -3.11 -B research/live_control/results/v13-v4-explicit-up-composition-c01-20261004/audit.py
```
