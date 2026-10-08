# WSLc cleanup evidence successor — Issue #7924

This package preserves the unregistered 2026-10-08 one-shot smoke failure and adds an offline, scoped cleanup-receipt contract test. It is not a retry and does not establish the original container's cleanup state.

The offline helper change emits the exact owned container ID, scoped query exit code, and raw response before classifying cleanup. See `UNREGISTERED_SMOKE.md` for the earlier incomplete evidence and `PROTOCOL.md` for H/T/D/C/U and strict no-runtime stop rules.

`REPORT.md` describes only the six-case receipt contract result. It must not be read as WSLc runtime or migration success.

From the repository root, reproduce the offline evidence with:

    python -B -m unittest -v research/analysis/wslc_cleanup_evidence_7924_successor_20261008/test_audit.py
    pwsh -NoProfile -File .github/scripts/test_wslc_cleanup_receipt.ps1 -OutputPath research/analysis/wslc_cleanup_evidence_7924_successor_20261008/results/candidate.json
    python -B research/analysis/wslc_cleanup_evidence_7924_successor_20261008/audit.py --candidate research/analysis/wslc_cleanup_evidence_7924_successor_20261008/results/candidate.json --output research/analysis/wslc_cleanup_evidence_7924_successor_20261008/results/audit.json

Formal output paths are exclusive-create. Do not rerun against an existing output or use these commands to invoke WSLc; the runtime smoke is explicitly outside this package.
