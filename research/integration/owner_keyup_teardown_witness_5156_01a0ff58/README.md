# Independent teardown witness review for #5156

Read [REPORT.md](REPORT.md) for the scoped coverage failure and
[PLAN.md](PLAN.md) for the prospective finite matrix. This is an additive,
retained-raw technical review of PR #6865; it never repeats A18/C01 or calls a
backend. The original files under `source/` are exact reviewed Git bytes.

Read-only reconstruction of the retained review, from this directory:

```sh
python -B -c "from pathlib import Path; from witness_audit import audit; import json; r=audit(Path('review-01')); print(json.dumps(r,sort_keys=True)); raise SystemExit(bool(r['errors']))"
```

Verify every published file against SHA256SUMS.txt before interpreting results.
The prospective FREEZE.json predates the assay. Later publication/validation
files are separately included in SHA256SUMS.txt and do not change that freeze.

For an explicitly separate ordinary construction, copy the package to a fresh
directory while omitting `review-01/` and `controls.json`; then run:

```sh
python -B probe_review.py
python -B witness_audit.py review-01
python -B review_controls.py
```

Do not reuse the retained output directory or reinterpret a reproduction as the
original invocation. No installation, container, live display, input or model is
required. Source-derivation files are for reading only. Five corruptions in
review_controls.py run against private temporary copies, preserving the source
evidence. The checksum manifest preserves mixed line endings and exact bytes.
