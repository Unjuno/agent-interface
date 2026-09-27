# Public API effect-gated recovery — Issue #4120

This additive study retains the first formal outcome for Issue #4120. It changes no shared runtime source.

Decision: `PASS_EFFECT_GATED_RECOVERY_BOUNDARY_SCOPED`.

Readable files include the preregistered plan/freeze, report, audit, environment and Git-object source manifest. The lossless evidence capsule retains the exact frozen experiment/auditor source, vendored runtime source, all excluded construction records and all formal case records/logs, but deliberately excludes ephemeral `Xauthority` cookie files.

## Read-only review

```sh
python -I -S -B unpack.py /tmp/ai4120-review
cd /tmp/ai4120-review
PYTHONPATH=vendor python -B audit.py formal --freeze FREEZE.json --controls --out /tmp/ai4120-review-audit.json
cmp AUDIT.json /tmp/ai4120-review-audit.json
PYTHONPATH=vendor python -B -m unittest -v test_audit
```

Do not rerun the consumed formal `run_matrix.py` allocation. A new measurement requires a separately frozen allocation.

Publication-helper failures and corrections are retained in `PUBLICATION_HISTORY.md`; they did not rerun formal measurement.

The provided execution environment was Linux x86_64 / CPython 3.13.5 with Tk/Xvfb/Python-Xlib available. Docker/OrbStack image identity was unavailable, so no Docker/OrbStack replication claim is made.
