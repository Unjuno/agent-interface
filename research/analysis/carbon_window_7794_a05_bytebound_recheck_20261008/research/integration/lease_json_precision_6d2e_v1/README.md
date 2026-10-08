# Retained lease JSON integer-representation boundary (#4435)

This directory publishes the already-consumed local allocation
`lease-json-precision-20260922-6d2e-01` without rerunning it.

- GitHub Issue: #4435
- Original intake main: `b2457b746a6df06f6536585dfe2ab937aff639f4`
- Publication intake main: `3666992ab2b5e1b41b159b361d1c690d8e720fdf`
- Tested repository Lease Git blob: `b9dac6bb4063928354733d79bf371909a288a3d1`
- Scientific disposition: `PASS_LEASE_JSON_REPRESENTATION_BOUNDARY_SCOPED`
- Formal rows: 1,062; formal invocations: 1; reruns/replacements/tuning: 0/0/0
- Formal raw SHA-256: `624d2b6434d2614fdb5d7001bec7b48904dc722fe1cf2e021a3e5673e6d357ba`

The result is a representation-boundary counterexample, not a production Node bug,
runtime promotion, GUI/model/task PASS, or natural failure-rate estimate.

## Result

Across 210 boundary cases per policy:

| policy | deadline changed | original reject -> LIVE | original LIVE -> reject/refuse |
|---|---:|---:|---:|
| PYTHON_DIRECT | 0 | 0 | 0 |
| NUMBER_ROUNDTRIP | 89 | 20 | 24 |
| BIGINT_AFTER_PARSE | 83 | 15 | 19 |
| SAFE_INTEGER_REFUSE | 0 forwarded changes | 0 | 60 original-LIVE refused |
| DECIMAL_TEXT | 0 | 0 | 0 |

The safe-integer policy refused 117 rows total. Twelve malformed decimal controls
were rejected before Lease invocation. The independent raw-only audit had zero
errors and rejected 12/12 rehashed semantic corruption controls.

## Chronology

The experiment, source freeze and first formal result preceded GitHub Issue #4435
because the earlier conversation exposed no usable GitHub write action. #4435 is a
retrospective evidence-delivery record; it is not public preregistration and does not
authorize a second scientific allocation.

The full original 47-file directory, including construction history, source,
raw JSONL, execution receipts, audit output and the historical publication STOP,
is retained losslessly in the archive parts in this directory.

## Verify full retained evidence without rerunning science

```bash
python verify_bundle.py /tmp/lease-json-6d2e-review
cd /tmp/lease-json-6d2e-review/research/integration/lease_json_precision_6d2e_v1
python -B -m unittest -v test_study
python -B audit.py results/formal-01 --controls --out REVIEW_AUDIT.json
```

The verifier only concatenates, hashes and extracts the retained archive. Do not
run `execute.py ... formal-01`; the allocation is consumed.

## Scope

Actual execution was on the supplied Linux x86_64 environment, CPython 3.13.5 and
Node 22.16.0. Docker/OrbStack image identity was unavailable. Exact integer clocks
were injected; this is not a real-clock drift/latency experiment. No model/provider,
GUI/input, package install, user data or experiment-time external network operation
was used.

#3880/#3886, #57 and the global ROADMAP remain open.
