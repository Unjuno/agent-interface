# Issue #4603 — read-only evidence reconciliation

## Disposition

Local read-only reconciliation **PASS**. Delivery to current `main` remains pending this PR; this is not a new scientific allocation and does not close #4284 or #4295.

The 60-case PR #4293 bundle is independently readable and internally consistent with its frozen manifest, source hashes, raw denominator, result summary, and corruption-control record. The distinct 24-row #4292 result remains present on the frozen delivery-main snapshot and is not merged or relabeled with the 60-case result.

## Frozen inputs and preservation

- Repository: `Unjuno/agent-interface`; intake `main` SHA: `d6dacd3507ea23a7c5aafe82788c0a9d8b452834`. During preparation, main advanced through `a1a9a7d0abdcdf65d5aba3b74e7f7caf171f2ca4`, `f5fdbcef6596e4d343492e1436642739566cae5b`, `3842e8921bd587af6ce9c13664d087b377366747`, `3c256e531ee0ef7d314fecd2c34217360b72c03c`, and delivery base `e786135bf5576f308c7d0185cfb484b9970bf6de`. The unchanged #4292 raw/report blobs were verified at delivery base; its `research/analysis` subtree SHA is still `c056b4f932d9d3ac60ffb16bc56800c088a8b3d4`, identical to the tree used for index generation. No files under `research/analysis` changed between index-generation base 3842e892 and delivery base e786135f. The PR branch was updated through GitHub's normal branch-update operation.
- Source PR #4293: head `393c4115add5e602ed279388a93dad4094daa687`, base `14cfdf1a5f31138b308f98fd0e80fa75e887e65d`; open and non-mergeable at intake. The head is not presented as current main.
- Issue #4284 and #4295 were both open at intake. No prior allocation was run, changed, replaced, or rerun.
- During this work, report-only PR #4612 was merged at `6fbd529f16d0ebe21548d1be3da83bac335ecba3`. It uses a distinct integration path and does not contain the 60-case bundle or independent verifier; this PR supplies those missing evidence artifacts additively without replacing #4612's report.
- All 18 files in PR #4293's changed-file list were read back from GitHub at the frozen PR head. Every computed Git blob SHA-1 matched the GitHub file record. Exact byte counts and SHA-256 values are retained in `READBACK.json`.
- The changed generated `research/analysis/README.md` in #4293 was read back and blob-verified, but it was not reused because it came from the stale PR base. Instead, `research/analysis/check_index.py` was read from delivery-base main and run exactly as prescribed with `--write` in a reconstructed analysis tree containing all 156 retained result directories from that commit plus this new report directory. Its generated README (34,734 bytes; Git blob `13581dcc5af1f26e89cdf0c7981528b5cc98b6bc`) then passed the same script's read-only check: `analysis index OK: 157 retained result/failure directories indexed`. The generated file is included in this PR; no hand-edited index entries were used.

## Independent read-only audit

The source bundle was reconstructed from the four retained Base64 parts, validated against each part's manifest length/SHA-256, Base64-decoded, and XZ-decoded in memory. The resulting 19-member tar was checked for duplicate/unsafe/non-file paths. No archive member was extracted to or written over predecessor paths.

- Decoded XZ archive: 10,640 bytes; SHA-256 `a35457c72f7dffed7351e2f6b9590744e3ab323418a462f413d7ea4f85a6711d`.
- `formal-01/RAW.json`: SHA-256 `711f67b0e615ec6b4fc58dddedd490724369b6476ff6036f52e34536e72114e9`.
- Eight frozen source hashes match independently between `FREEZE.json`, `EVIDENCE_MANIFEST.json`, and the archive members.
- Independent raw checks: 60 unique cases; full 3 policy × 10 schedule × 2 repetition matrix; 462 lifecycle rows; input-predicate truth and guarded-graph mapping; row/case authority false; activation identity/shadow floor; novelty fallback; identity invalidations; UNKNOWN preservation; call-accounting consistency; and stable-active GENERAL ratio 8/32 = 0.25.
- The frozen formal control report records 13/13 tamper controls rejected. A separate implementation in `verify_evidence.py` recreated those 13 mutation classes and its own raw checks rejected 13/13.
- The deliberately unsafe unguarded diagnostic comparator has four semantic mismatches in retained rows; these are expected comparator evidence, not candidate-policy failures. The baseline and candidate rows satisfy the independent predicate/graph checks.
- Frozen formal result remains 1 invocation, 0 reruns, 0 replacements, 0 tuning, authority false. The formal runner was not executed.

The audit ran in Docker Desktop Engine 28.5.1, image `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, with `--network none --read-only`; only bounded `/tmp` was writable. The source readback was mounted read-only. Machine-readable outcome is `INDEPENDENT_AUDIT.json`.

## Distinct 24-row control

On delivery-base main, #4292's `research/analysis/predicate_specialist_switch_4284_v1/FORMAL_RESULT.json.zlib.b64` had Git blob `92a32126cc76e4e663d7604ba454b666ec95b356`, identical to the merged #4292 file record. Its independently Base64/zlib-decoded bytes hash to `dbf74500b348c9a3503e0dd489bb04d9d00f5d6a47a0c9163d4cc615ea90bb31`; decoded timeline length is 24. The #4292 report file blob also matches its merged-PR file record (`6b7065deca1ba5e3a252964c0e27cb9905e257d0`).

The 24-row baseline and 60-case result remain separate. This audit does not answer the regeneration-versus-lifecycle call-count question in #4295, does not make either predecessor issue complete, and makes no learned-model, live-task, token, runtime, or product claim.

## Reproduction

From a checkout of the reconciliation PR on current main, run the verifier with the preserved #4292 control path:

```powershell
docker run --rm --network none --read-only `
  --tmpfs /tmp:rw,noexec,nosuid,size=8m `
  -v "${PWD}:/repo:ro" -w /repo `
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 `
  python research/analysis/versioned_predicate_specialist_switch_4284_reconciled_4603_v1/verify_evidence.py `
  research/analysis/versioned_predicate_specialist_switch_4284_reconciled_4603_v1 `
  --control24 research/analysis/predicate_specialist_switch_4284_v1/FORMAL_RESULT.json.zlib.b64
```

No formal runner, model/provider, GUI, or OS input is invoked.

The verifier was also exercised with the repository root as its input and no explicit `--control24` argument; it resolved the delivered reconciled package and the separate #4292 control path correctly. Both package-directory and repository-root invocation modes return the same read-only reconciliation report.
