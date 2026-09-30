# Verifier registry T0 — Issue #5273

Finite, authority-neutral compatibility preflight for a versioned descriptor snapshot. The frozen #5268 IR and #5269 candidate remain untouched. Costs are synthetic planning estimates, never measured latency; all dispatch counts are zero.

Reproduce host construction only:

```sh
python3 -m unittest -v
python3 freeze.py
python3 run_formal.py
python3 audit.py
```

The freeze command shown above recreates the manifest; for the retained run use the already committed `FREEZE.json` and run only the last two commands. Formal container execution is separate and was STOPped because no exact shared resource lease was granted. Host construction does not substitute for a container result.
