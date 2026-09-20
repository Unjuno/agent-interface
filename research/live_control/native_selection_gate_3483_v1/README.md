# Inkscape selection-gated save evidence

Issue #3483: one fresh arm64 OrbStack allocation (seed 991131). See `REPORT.md` for H/T/D/C/U and scope, `PLAN.md` for the frozen experiment, and `audit.json` for the independent result.

`evidence-991131.tar.gz` contains the full retained allocation bundle and these audit/plan files. Extract with:

```sh
mkdir evidence-991131
tar -xzf evidence-991131.tar.gz -C evidence-991131
```

The read-only `audit.py` checks source/request/reply hashes, SVG geometry, release state, and Docker lifecycle via the named OrbStack container. Re-running it requires that container to remain available; the computed outcome and evidence manifest are frozen in `audit.json`. Raw false cleanup-receipt booleans are preserved; the report's independent process-termination check is separate.
