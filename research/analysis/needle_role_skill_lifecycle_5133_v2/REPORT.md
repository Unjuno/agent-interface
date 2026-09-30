# Role-skill lifecycle amortization (-04) — scoped PASS

Issue #5133; successor lineage #5084 / #5053. Allocation:
`needle-role-skill-lifecycle-4916-larger-rung-20260928-04`.

## H / T / D / C / U

**H.** For the exact retained synthetic seed-3788 role-skill package, per-request
read/parse/digest/schema/shape validation and selected-role construction costs
more across 1,000 requests than one complete load/validation/all-role
construction followed by role reuse, with identical predictions.

**T.** Fifteen paired blocks, alternating AB/BA order. Each arm processes the
same fixed 1,000-request A/B/C schedule per block. `RELOAD_EACH_REQUEST`
repeats full loading, validation, selected-role construction and prediction;
`LOAD_ONCE_REUSE` includes one full validation/all-role construction in its
initialization lifetime cost and then scores with retained role models. Startup
is excluded equally. The formal raw contains 30,000 predictions total.

**D.** `PASS_LIFECYCLE_AMORTIZATION_SCOPED` requires exact frozen identity,
12,288/12,288 construction parity, 30,000/30,000 independently reconciled
formal predictions, zero raw-audit errors, rejection of all seven frozen
corruptions, at least 12/15 reuse wins, median lifetime ratio <=0.90, and
median first cumulative break-even request <=1,000 (non-crossings censored at
1,001). All gates passed. The independent audit result is the decision source.

**C.** Same package, schedule, scorer, process boundary, pinned image and CPU
limit; lifecycle is the intended treatment. Network disabled; root/source
read-only; only dedicated output mounts writable. The auditor runs separately
and reconstructs predictions using its independent float32 oracle; it does
not import the candidate.

**U.** One synthetic seed/package and pure-Python scorer only. This is not a
model fit, live/real-time fine-tuning, LoRA quality or GPU result, natural-
language routing test, role-network task-success result, GUI effect, production
latency or product claim. It does not close #4916.

## Frozen identity and outcomes

- Base main: `3007e03481d545eb9a92b8cec07c8c4201bd3728`.
- Image: `python:3.13.5-slim-bookworm`, ID
  `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`,
  linux/amd64, Docker Desktop `desktop-linux`.
- Freeze SHA-256:
  `2a9b6e327a02e67f5e9b7d4bce42515a69157b47ecdaac1fb1a04f085fd9f118`.
- Construction: exit 0, `CONSTRUCTION_PASS`, 7/7; candidate and independent
  oracle each reproduce all 12,288 retained predictions. Receipt SHA-256
  `ca84d54a70a44c682e58aee777a6e6dc2b19d895f97e623a7720969c6b6b5da`.
- Formal: exit 0, `RUN_COMPLETE`; 15/15 blocks, 1,000 requests/arm/block,
  15,000 predictions per arm and 30,000 total. Raw SHA-256
  `9e9a0ef349a08f69d01b7e97756b3e02d6691e835c024380f1b8da876524ab65`.
- Independent audit: exit 0, `PASS_LIFECYCLE_AMORTIZATION_SCOPED`; errors 0,
  semantic mismatches 0, 30,000 predictions reconciled, reuse won 15/15 pairs,
  median lifetime ratio `0.0480300872553996`, median first break-even request
  `1`, seven of seven mutation controls rejected. Audit SHA-256
  `c722dfc0694963b479e1930cf6605dceaa04c5c54f8e3efa5e4f6e290e8f0545`.
- Decision: scoped PASS. Keep #5084/-01, #5084/-02 and #5133/-03 construction
  STOP unchanged; -04 is an additive corrected allocation.

See `FREEZE.json`, `INVOCATION_LOG.md`, and `results/{construction-04,formal-04,audit-04}/`.

## Post-review evidence correction — append-only

The original `audit-04/audit.json`, raw formal output, and frozen sources are
preserved byte-for-byte. Review found that the original auditor seeded both
cumulative-cost accumulators with the reuse initialization cost, cancelling
the required initialization charge in its break-even calculation. It also
reported stale 5-block/40-request scope metadata. Therefore the original
`PASS_LIFECYCLE_AMORTIZATION_SCOPED` is superseded for promotion purposes; its
historical bytes remain unchanged. The formal raw has **not** been rerun.

`audit_correction.py` is a separately versioned, post-review read-only
reconstruction over the same immutable raw. It charges initialization only to
reuse, rebuilds all predictions with the independent oracle, checks frozen
identities and mutation controls, and derives scope from the raw sample counts.
Its report is additive at
`results/audit-correction-04/correction.json`; it does not overwrite the
original audit or claim a new formal allocation.

The original analysis-index CI failure was independently reproduced locally
and fixed by refreshing `research/analysis/README.md`;
`python research/analysis/check_index.py` passes with 192 retained
result/failure directories indexed.

## Correction: published source bytes and CRLF preservation

The preceding source-hash interpretation was incomplete. Direct raw-byte
readback at PR head `465f6315074f6f98df3789a6936aafacf03e9409` confirms that
the five Python sources were stored as LF-only Git blobs while the frozen
SHA-256 values and formal raw identify the original Windows worktree's mixed
line-ending bytes. Removing only CRLF carriage returns makes each local source
byte-for-byte equal to the corresponding GitHub raw file (5/5). The Git blob
IDs in the original FREEZE match the normalized LF blobs, but those IDs alone
did not reveal the working-tree byte mismatch. Thus the source text and measured
Windows bytes agree; the published checkout bytes were not reproducible and
the original independent audit correctly STOPs from a Linux checkout.

This successor correction adds a path-scoped `-text` rule so the exact
measured source bytes survive fresh clones on Windows and Linux. The frozen
FREEZE, formal raw, original audit, and their historical hashes remain
unchanged. The new raw-only correction report records the exact-byte Git blob
IDs as well as the frozen SHA-256 values. The previous source-hash discussion
above is superseded by this line-ending diagnosis.
The exact source bytes have now been restored into the Git tree under a
path-scoped `-text` attribute. See `SOURCE_BYTES_REPAIR.md` for the original
and exact-byte Git blob IDs and the unchanged frozen SHA-256 manifest.
