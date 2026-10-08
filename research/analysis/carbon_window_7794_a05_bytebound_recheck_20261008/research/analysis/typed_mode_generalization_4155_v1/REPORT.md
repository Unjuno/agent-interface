# Formal result — Issue #4844 successor to #4155

## Disposition

**FAIL_MODE_MISROUTES_RECOVERY**, exactly under the frozen decision hierarchy. The raw-only independent audit found zero provenance, row-generation, or prediction errors across 4,800 held-out rows. However, one of 15 complete deterministic prototype controls failed exact cross-arm/action agreement: at seed 415581, LAYOUT_CHANGED (`[0,0,0,0,1,0]`) expected REOBSERVE; DIRECT_RECOVERY conservatively emitted YIELD at posterior 0.630456960871 (<0.65), while MODE_THEN_RECOVERY emitted REOBSERVE at posterior 0.778274566680. This is an abstention/prototype mismatch, not evidence of an unsafe GUI action. The frozen control gate nevertheless fails. No retry or post-result change was made.

## Frozen partial/composition gates

Pooled descriptive counts across the three formal held-out seeds (960 rows/block):

| Block | Direct wrong recovery | Mode wrong recovery | Relative reduction | Direct safe coverage | Mode safe coverage | Coverage loss | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| SINGLE_MISSING | 165/960 (17.1875%) | 180/960 (18.7500%) | -9.09% | 12.0833% | 18.5417% | -6.4583 pp | Fail |
| MULTI_MISSING | 89/960 (9.2708%) | 73/960 (7.6042%) | 17.98% | 26.6667% | 28.9583% | -2.2917 pp | Fail: below 25% |
| COMPOSITION_HOLDOUT | 219/960 (22.8125%) | 222/960 (23.1250%) | -1.37% | 13.1250% | 22.8125% | -9.6875 pp | Fail |

Negative coverage-loss values mean the mode arm had higher safe recovery coverage. The one modest multi-missing reduction is below the preregistered 25% threshold. Single-missing and composition-holdout wrong recovery are slightly higher for the mode arm. Consequently no primary partial/composition block meets PASS.

Other controls: all-missing unknown YIELD 3/3; contradictory-input YIELD 3/3; full prototype exact cross-arm/action match 14/15. Independent audit: `errors=[]`, 4,800 unique held-out rows, terminal status `FAIL_MODE_MISROUTES_RECOVERY`.

## Execution and provenance

- Formal support seeds: 415571, 415572, 415573; held-out seeds: 415581, 415582, 415583. The allocation was run exactly once.
- Local Docker image: `python:3.13.5-slim-bookworm`, ID `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`, linux/amd64.
- Runner: CPU-only, `--pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64 --security-opt=no-new-privileges`; source mounted read-only and fresh output directory separately mounted writable. Exit 0; 4,800 rows; raw SHA-256 `c93dcf94912364784c53d8ae1baa35624839ea239cc0974ab8a08daa7211877c`.
- A separate local CPU Docker invocation audited the raw file read-only; only a distinct audit-output directory was writable. Exit 0; 4,800 rows; 0 errors; audit JSON SHA-256 `1064aca45d02fcf9b8fe9fe08dbbeb8f4c2861fe18c90a67bab270e96d6bd046`.
- Lossless raw retention: original `raw.json` is 3,298,585 bytes (SHA-256 above); deterministic gzip archive is 207,697 bytes, SHA-256 `c9f2eb711105342a9f7c7faf502a96a900db9a35c3dc1d242ec0419252b54857`. GitHub handoff stores the gzip bytes as five consecutive base64 chunks under `formal/raw.json.gz.b64part-*`; concatenate chunk text in order, base64-decode, then gunzip. Verify both the gzip and reconstructed raw SHA-256 values before use.
- No GitHub Actions/workflow ran the experiment. No GPU was requested or used.
- Construction suite before formal freeze: 6/6 passed. Pilot and all construction failures remain separately preserved; neither was pooled with formal rows.

## Interpretation and next decision

This one synthetic authored fault family does not support the preregistered generalization claim. The mode factorization slightly improved safe coverage but failed to reduce wrong recovery enough, and its complete-observation control disagreed once because direct classification abstained. It does not establish real GUI behavior, cross-app transfer, runtime safety/authority, user benefit, or efficiency. Retain this result unchanged; any follow-up must be a separately preregistered successor with a material hypothesis/design change, not a retry or gate relaxation of this allocation.
