# Retained WSLc receipt audit v2 — #3352 / #7020

Additive saved-data engineering repair. See [REPORT.md](REPORT.md) for outcomes,
first failures, exact scope and handoff. The original [qualified T0/T0A package](../wslc_dockerfile_build_smoke_t0_20261003/)
remains unchanged; its declared formal T0A gate remains not established.

Read-only checks from the repository root:

```sh
python3 -B research/analysis/wslc_receipt_audit_v2_3352_01a10197/verify_repair.py
python3 -B -m unittest discover -s research/analysis/wslc_receipt_audit_v2_3352_01a10197 -p test_repair.py -v
python3 -B -O -m unittest discover -s research/analysis/wslc_receipt_audit_v2_3352_01a10197 -p test_repair.py -v
python3 -B research/analysis/wslc_receipt_audit_v2_3352_01a10197/audit_v2.py --root research/analysis/wslc_dockerfile_build_smoke_t0_20261003
```

The last command is an ordinary v2 saved-data check, not the original formal T0A.
Do not run `run_regressions.py` on this retained output path: it refuses existing
`cases/`. For new ordinary construction, copy the sources to a fresh sibling package
with access to the same pinned old package. The literal first runner and extension
construction commands are preserved as `.py.txt` snapshots; the extension snapshot
includes its historical checker repair and should be inspected rather than replayed.
No container, OS input, model call or original producer is invoked by these checks.
