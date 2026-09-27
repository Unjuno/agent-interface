# Score coverage boundary (#4356)

A synthetic statistical result about nominal marginal intervals, simultaneous
coverage and possible-max candidate retention. Read REPORT.md for measured
results and PLAN.md for the preformal H/T/D/C/U, proofs and variable/unit table.
This is not a GUI detector, action-admission component or production threshold.

## Read-only reproduction from committed files

From this directory with CPython3.13:

```sh
python3 -S -B verify.py
python3 -S -B -m unittest -v test_contract test_restore
```

verify.py verifies MANIFEST.json, reconstructs the exact807398-byte RAW in a
fresh temporary location, checks actual original process/outer/audit receipts,
and reproduces original raw audit and controls stdout byte-for-byte. It does not
invoke formal simulation. Temporary restored data are removed after verification.

To retain decoded original RAW for independent inspection, use a nonexistent
file in an existing trusted directory:

```sh
python3 -S -B restore.py /tmp/score4356-original-RAW.json
python3 -S -B audit.py /tmp/score4356-original-RAW.json
```

Do not rerun consumed execute.py or run.py. Source/gates were publicly fixed
before the single formal allocation. Different audit processes are read-only
verification, not new samples. Original formal01 receipts/stdout/stderr and all
source files remain directly reviewable. Large RAW is losslessly encoded using
PACK.json and RAW.columns.part00.b64 through part08.b64; no RNG or policy is
executed during decoding. Missing/corrupted/reordered parts fail closed.

## Integration boundary

All files are additive under research/observation_gating/score_coverage_k9m2_v1.
No runtime/default, workflow, root README/ROADMAP, historical source or foreign
branch is changed. #4276, #2751 and #2789 remain separate. Merge this as research
evidence only, subject to fixed-head checks/review and exact Git-object readback.
