# Retained WSLc receipt schema audit — #5309 T8

Status: frozen offline-only successor validation. It does not rerun the T6 candidate, T7 WSLc auditor, Docker, WSLc, or any application. It does not change T7's `STOP_HOST_RECEIPT_SCHEMA_MISMATCH` disposition.

- Successor Issue: [#6990](https://github.com/Unjuno/agent-interface/issues/6990)
- Predecessor migration Issue: [#6975](https://github.com/Unjuno/agent-interface/issues/6975)
- Immutable T7 evidence: [draft PR #6983](https://github.com/Unjuno/agent-interface/pull/6983), head `684831240f9848e850736781edb98322949e8d8a`
- T7 captured stdout Git blob: `588d1816282ab17790faa3a94a939f9fce8d8bc3`
- Allocation: `WSLC-RECEIPT-5309-T8-20261003-01`
- Branch: `research/wslc-receipt-schema-5309-t8-20261003`
- Additive result path: `research/analysis/wslc_receipt_schema_5309_t8_20261003/`

## H / T / D / C / U

**H.** The exact retained 306-byte T7 stdout is valid JSON with 432 rows, 432 unique cases, 432 independent row matches, semantic digest `a7bd0adc9485df7161b7ce85c27b1dc58fad71ee2fee9cfe081cc61337b0e193`, task-fallback wrong-target count 27, yield-fallback count 0 under the auditor's actual field name `failed_probe_yield_wrong_target`, zero authority grants, and no errors. A new strict offline validator can certify these receipt facts and expose the frozen host-verifier key mismatch without revising T7's result.

**T.** Copy only the captured stdout from PR #6983 into `input/audit.stdout.json`, verify its byte count/SHA-256 and provenance, freeze a standard-library validator and mutation tests, then invoke the validator once to emit `formal_validation.json`. Tests must reject altered input identity, key set, counts, status, and errors. The validator accepts no external JSON package, model, GUI, network, or runtime. No candidate, WSLc/Docker container, or additional receipt-validation CLI call is allowed.

**D.** `PASS_RETAINED_RECEIPT_SCHEMA_AUDIT` only if input identity is exactly 306 bytes/SHA-256 `604fc18e94e80f6aa941623b8854ffad88043e16e5058db89aa45449ba97489f`; all nine frozen fields and strict types/values match; the single CLI run emits the pass receipt; mutation tests reject each frozen corruption; and T7/T6 source and evidence remain unchanged. Any mismatch is retained as the first STOP/FAIL, with no retry.

**C.** This is an offline audit of captured output, not a replacement for T7's frozen host verifier or a re-run of T7's auditor. Even a T8 pass confirms only that the retained stdout carries the preregistered values under the actual schema. T7's official STOP remains unchanged.

**U.** No Docker/WSLc/native-WSL comparison, timing, memory, resource-cap, candidate/model/GUI/application-effect, or general migration claim.

## Frozen command

From this package directory, after committing `FREEZE.json`:

```powershell
python -B validate_receipt.py input/audit.stdout.json formal_validation.json
```

The command is one-shot and output creation is exclusive. The validator will not overwrite a pre-existing receipt. `python -B -m unittest -v test_validate_receipt.py` is a construction/mutation test only; it does not invoke the formal CLI or read/write the formal output.
