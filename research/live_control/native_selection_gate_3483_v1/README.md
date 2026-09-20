# Inkscape selection-gated save evidence

Issue #3483: one fresh arm64 OrbStack allocation (seed 991131). See `REPORT.md` for H/T/D/C/U and scope, `PLAN.md` for the frozen experiment, and `audit.json` for the independent result.

`evidence-991131.tar.gz` contains the full retained allocation bundle and these audit/plan files. Extract with:

```sh
mkdir evidence-991131
tar -xzf evidence-991131.tar.gz -C evidence-991131
```

`audit.py` and `audit.json` are the original producer-side audit record. **Do not rerun `audit.py`**: that legacy script calls `docker inspect` and rewrites `audit.json`; the named container may no longer exist. The raw archive and frozen audit are retained unchanged.

For portable, read-only recomputation, run `python3 audit_replay.py /path/to/extracted-bundle`. It writes JSON only to stdout and does not invoke Docker or alter the bundle. It independently checks the 62 frozen manifest entries, request/reply/source lineage, verified-empty releases, and saved SVG geometry. It labels visual-review and container-lifecycle fields as attestations from the frozen producer audit; the archive does not contain a portable Docker inspect receipt, so offline replay does not claim independent lifecycle verification or perform a new visual inspection. The original raw cleanup false flags remain unchanged.
