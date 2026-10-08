# Read-only A06 execution record

The pre-run source snapshot comes from A04 commit
`2e5641aea33a204bc27681abf70c2d619302b6cf`; the complete separately archived
formal output comes from PR commit `a422c3d49902a2bc424d80b4fd4c41ef45aa2996`.
The pinned base-tree mapping was read from commit
`a9352dc53c783f1501046d762bc36c34bc6ab480`. A05's earlier harness STOP is
retained in `inputs/A05_FIRST_ATTEMPT.json`; A06 is a new reader version.

Commands, from this directory:

```powershell
python -B audit_readonly.py
python -B -m unittest -v test_posthoc_audit.py
```

The reader writes only `AUDIT.json`. Tests exercise temporary input copies. The
retained A04 candidate and formal auditor are read as data and are never
invoked. No container, X11 server, application, model, game, or input path was
started.
