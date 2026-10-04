# V39 unknown outer-event adapter evidence — A01

## H / T / D / C / U

- **H:** The frozen V39 projector ignores an event whose outer `event` name is unknown, even when that row carries `physical_key_measurement` for the same identity as a valid DOWN/UP pair. A duplicate can therefore be hidden while the projector reports complete timing. Any row carrying adapter-measurement evidence must invalidate completeness unless its outer event kind is explicitly supported.
- **T:** Against exact #7602 parent source `a7f9e9e3c4bd31199bde3a14761783ead619ad08`, run one isolated regression method on the retained V39 raw fixture. Preserve a unique-pair positive control and three negative cases: unknown-name duplicate DOWN, unknown-name duplicate UP, and an unknown-name measurement row by itself. First run the test on baseline to confirm the bug, then apply the smallest source fix and run the same frozen test once; separately audit the retained raw results.
- **D:** Baseline must show exactly three assertion failures across the three negative cases and no test errors. The patched candidate passes all three negative cases with one `adapter_edge_receipt_incomplete` receipt and both timing intervals null; the unique supported DOWN/UP pair remains paired. Source/test byte-compilation and the independent raw-result audit must pass. Any different failure is retained as a construction STOP/FAIL and is not relabeled.
- **C:** Forward compatibility might prefer ignoring unknown event types. Here, silently discarding nested adapter evidence permits a false complete receipt; rejecting only rows that carry `physical_key_measurement` is the bounded fail-closed alternative. A malformed or missing identity may still be unable to join and remains an explicit evidence limitation.
- **U:** One retained synthetic trace and a pure projector only. No live X server, physical key, application consumption, game, model, GUI, useful task effect, recovery, or MAP01 completion is measured. This is a construction regression and does not authorize the gated live allocation.

## Frozen execution

- Parent implementation: #7602 head `a7f9e9e3c4bd31199bde3a14761783ead619ad08`, controller blob `7494e8f217dc86e94cb1bca2fd37475cd53b7e9c`.
- Test and retained fixture bytes are copied under `src/` and SHA-bound in `RED_FREEZE.json` and `GREEN_FREEZE.json`.
- Runtime: cached Linux/amd64 image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, `--pull never --network none --cpus 1 --memory 512M`; source/evidence read-only and a dedicated output mount. WSLc swap enforcement is observed and reported, not inferred.
- Maximums: one baseline red check, one corrected construction check, one independent audit; retries 0. No model, game, GUI, OS input, GPU, external network, or package install.

## Outcome addendum — 2026-10-05

- Baseline regression outcome: `raw/red-result.json` is `EXPECTED_RED`, with exactly three assertion failures and zero errors across the unknown-duplicate-DOWN, unknown-duplicate-UP, and unknown-only-measurement cases.
- Candidate regression outcome: `raw/green-a02-result.json` is `PASS`, with one test method, three cases, zero failures/errors, and `py_compile: PASS`. The source, test, fixture and runner hashes are pinned in `src/green_freeze_a02.json`.
- The candidate pre/post WSLc inventory receipts in `raw/` show 205 terminal rows and identical container ID sets. The independent-audit invocation's separate A05 pre/post resource receipts show 211 terminal rows and identical ID sets; `audit-a05/postflight-resource-check.json` covers resource inventory only.
- The independent raw audit is **STOP**, not PASS. Earlier auditor protocol failures remain in `audit/` and `audit-a03/` through `audit-a04/`. The final A05 auditor validated the frozen input hashes, then failed its mutation-control assertion because the source-hash mutation is not checked by its `validate()` function. See `audit-a05/auditor-container.log` and `AUDIT_A05_PLAN.md`. No regression test was rerun for these auditor revisions.
- WSLc repeatedly warned that swap-limit capabilities/cgroups are unavailable. The configured memory cap is not described as swap-bounded.
- Scope remains one retained synthetic trace and a pure projector. No live input, GUI/game run, physical key release, application effect, recovery benefit, or MAP01 completion is established.
- Package disposition: the candidate behavior is a scoped construction PASS; the separate independent-audit gate is STOP. Do not treat the audit as passed or promote this evidence to a live-control or product claim.
