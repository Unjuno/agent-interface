# MAP01 owner pagination integrity T1

Disposition: **PASS_BOUNDED_FAIL_CLOSED_GAP_FOUND**. The retained current-main owner helper admits at least one synthetic incomplete run set whose `total_count` equals the visible row count because duplicate IDs conceal an omitted distinct run. Independent raw audit: **PASS**, 44 cases, 5 counterexamples, no audit errors.

Run from the repository root with Python 3.13+:

```sh
PYTHONPATH=/tmp/map01-owner-pagination-source python3 research/analysis/map01_owner_pagination_integrity_59_t1_20261001/candidate.py research/analysis/map01_owner_pagination_integrity_59_t1_20261001/raw.json
python3 research/analysis/map01_owner_pagination_integrity_59_t1_20261001/audit.py research/analysis/map01_owner_pagination_integrity_59_t1_20261001/raw.json
python3 -m unittest discover -s research/analysis/map01_owner_pagination_integrity_59_t1_20261001 -p 'test_audit.py' -v
```

The frozen source module and its existing test were retrieved byte-for-byte from main intake commit `5eb0c44f2fc3d851b6469ceabda57b091ec76668` into `/tmp/map01-owner-pagination-source/` (candidate SHA-256 `0b1056c6cbd95288d2c1934a471d2a04b9c000cd1114da7a49310afc850b87fd`; test SHA-256 `f72f369e2e3d9697108ae905894da33f92198fc2aa7e30abaa84d7efb5838dc6`). Existing helper tests: 12/12 pass. Candidate module, test and audit syntax compilation and `git diff --check` pass. Candidate raw SHA-256: `67c910b3ea5821c4f561f92464698829213ee8757be33612682b6784c705c5da`.

## Limits

This is a synthetic parser/contract counterexample. It does **not** demonstrate that GitHub Actions actually returns duplicate run IDs across pages while its `total_count` equals raw visible rows. No external API request, Actions dispatch, workflow, game, model, GUI, OS input, Docker, or GPU was used. The correct next determination is whether the actual workflow API response contract guarantees unique IDs and whether the workflow itself fails closed on incomplete pagination. No live allocation is authorized by this result.
