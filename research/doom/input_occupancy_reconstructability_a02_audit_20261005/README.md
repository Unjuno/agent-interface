# A02 raw-derived audit of retained per-key occupancy census

## H / T / D / C / U

**H.** The A01 summary fields for physical-down receipts, per-key up measurements, and actuation IDs can be independently recomputed from its frozen V38/V39 event streams; corrupted summary values must fail the audit.

**T.** Recompute every material run-summary field from the frozen A01 result inputs: report, event stream, and owner ledger. Compare all recomputed counts and identity lists with the retained A01 `RESULT.json`. Mutation controls forge per-key down/up counts and IDs, forge owner-release counts, claim reconstructability without edge records, and use duplicate actuation IDs.

**D.** `PASS_RAW_DERIVED_AUDIT` requires the clean A01 result to match the raw-derived values exactly and all mutation controls to be rejected by non-empty audit errors. The old A01 `AUDIT.json` is not treated as authority for fields that it does not recompute.

**C.** A01 remains `FAIL_INSUFFICIENT_PER_KEY_EDGE_EVIDENCE`: the retained raw V38/V39 streams have no identity-linked physical-down brackets or per-key up measurements; both runs retain verified-empty aggregate terminal releases. A02 tests audit binding and leaves all A01 outputs unchanged.

**U.** This is a posthoc records audit only. It does not imply stuck input or unsafe behavior, identify physical edge times, establish useful feedback, recovery, threat response, or MAP01 effect. No game, model, GUI, X server, OS input, or allocation was run.

The earlier A01 auditor's false-pass result for fabricated per-key summary values is preserved in `BASELINE_MUTATION.md` and `results/a02/A01_BASELINE_MUTATED_{RESULT,AUDIT}.json`; no A01 source or output was rewritten.

## Reproduction

Run from the repository root with the frozen Python runtime and no network:

```sh
docker run --rm --network none -v "$PWD:/audit" -w /audit python:3.11.9-slim \
  python -B -m unittest -v research.doom.input_occupancy_reconstructability_a02_audit_20261005.test_audit
docker run --rm --network none -v "$PWD:/audit" -w /audit python:3.11.9-slim \
  python -B research/doom/input_occupancy_reconstructability_a02_audit_20261005/audit.py
```

The tested image was `python:3.11.9-slim`, digest `sha256:8fb099199b9f2d70342674bd9dbccd3ed03a258f26bbd1d556822c6dfc60c317`. `FREEZE-A02.json` pins the parent A01 result, source scripts, manifest, and all retained raw inputs; `SHA256SUMS.txt` pins this A02 package and captured outputs.
