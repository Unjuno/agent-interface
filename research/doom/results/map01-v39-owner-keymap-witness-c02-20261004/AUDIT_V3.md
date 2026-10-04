# C02 temporal audit v3 — root-shape fail-closed companion

This additive audit version closes the valid-JSON root-shape gap found after
PR #7419's v2 report-boundary repair. The original v2 source, test file,
`AUDIT_V2.json`, and retained candidate/input bytes are unchanged.

## Finding and repair

With `candidate.raw.json` containing the valid JSON value `null`, v2 catches the
parent evaluator's `AttributeError`, then raises another `AttributeError` when
its temporal evaluator calls `.get()` on `None`. Because this happens before
the report write, a previously seeded PASS report remains on disk. The regression
test records that exact main-entry-point behavior.

V3 validates that both raw and cases roots are JSON objects before delegating to
the frozen v2 temporal helper. Invalid roots become explicit failed checks and
produce `AUDIT_V3.json`; v3 never writes `AUDIT_V2.json`. For the retained object
raw, v3 reuses the exact v2 temporal helper and original parent audit. This is a
supplemental report-boundary repair and audit, not an independent implementation
of the temporal predicate.

## One-shot audit record

- Source/head reviewed: `4346b4c92c44593ef26ea366e1d9f8234f580bf6` (PR #7419).
- Host/runtime: Windows, CPython 3.11.9.
- Command, from this directory: `py -3.11 audit_temporal_v3.py`.
- Started: `2026-10-04T03:54:27.4248437Z`; exit code: `0`.
- Result: `PASS_V39_XVFB_KEYMAP_TEMPORAL_BINDING_V3_SCOPED`, all 10 report checks
  true; no failed checks or evaluator errors.
- Candidate raw SHA-256: `80deae01ca6167c91c66e70d725be290b7959750dc1c76e1f344d9f18014e453`.
- V3 auditor SHA-256: `a68f8572d8a51c186f69d13b934e7ec81b49fbdacfc402b1c41bf73e4ad48606`.
- V2 helper SHA-256: `b3e00b8660789e72ae3b313ca0082e597b9af48e03e683f28643219e56c23a5b`.

The supplemental audit read retained raw/input files only. Candidate execution,
Xvfb, MAP01, model/provider calls, GUI, and input were not run. The synthetic
null-root control and a valid synthetic positive control are covered by
`test_audit_temporal_v3.py`; the combined v3, v2, and parent test modules pass
19/19. This result does not establish physical key occupancy, application
delivery, task usefulness, live safety, recovery efficacy, or MAP01 completion.

See `AUDIT_V3.json` for checks and `AUDIT_V3.stdout.txt` for the captured command
output. `AUDIT_V3_SHA256SUMS.txt` binds these files and the unchanged v2 inputs.
