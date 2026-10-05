# Read-only A05 execution record

This program reconstructs retained A04 bytes only. It never imports or invokes the A04 candidate or formal auditor. The pre-run source snapshot comes from A04 commit `2e5641aea33a204bc27681abf70c2d619302b6cf`; the separately archived formal output comes from `aa4b4a4cf68eb795340d4182c240833d37b910a2`. The pinned base-tree mapping was read from commit `a9352dc53c783f1501046d762bc36c34bc6ab480`.

Commands, from this directory:

```powershell
python -B audit_readonly.py
python -B -m unittest -v test_posthoc_audit.py
```

The auditor writes only `AUDIT.json`. Tests exercise copies in temporary directories. No candidate, original auditor, container, X11 server, application, model, game, or input was started. The original candidate exit and auditor exit are read from the retained files and are not rerun.
