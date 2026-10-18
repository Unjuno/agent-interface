# Issue #5665 T1 audit eligibility-gate successor (A02)

## Outcome and scope

A02 reproduces a narrow audit-gate defect in the retained synthetic #5665 T1 archive. The unchanged v2 audit reports `PASS` after one of its 200 IID rows becomes nonexchangeable. Its top-level `eligible_iid_rows` is the pre-filter scheduled IID count (200), while `decision.iid_replicates` and an independent raw-only eligibility reconstruction both equal 199. The baseline reports PASS and 200 throughout. This does not establish an empirical failure-yield claim, disprove the estimator, or alter the prior T1 result; it shows that the prior PASS did not enforce the stated all-200-eligible requirement under this mutation.

A01 separately stopped before target invocation because its first runner tried to create output under a read-only source mount. It was not retried; the stop is recorded in #5665 comments. A02 used a distinct freeze with output mounted writable at `/output`.

## H / T / D / C / U

**H:** The existing audit can PASS after one IID row is correctly reclassified HOLD, despite the preregistered requirement that all 200 IID rows remain eligible.

**T:** Reconstruct the retained 204-row raw JSONL, mutate only seed 5665002 / `iid-001` by changing `validation_stratum` to `mutation-shifted-validation-stratum` and candidate disposition to `HOLD_NONEXCHANGEABLE`, then invoke the frozen v2 audit once each on baseline and mutation.

**D:** Baseline must PASS with 200 eligible. Defect reproduced if mutation also PASSes and reports 200 scheduled IID rows, but independently classified eligible IID count is 199 (the audit's `decision.iid_replicates` is 199). A02 met this condition. No retries.

**C:** WSLc 3.0.1.0; Python 3.12.15 image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`; pull never, network none, CPU 1. Frozen audit Git blob `c8de1110855c0886b142ec0400677120b9f6a216`, SHA256 `d4f4f862039af5b568be5b9e2a94b64a42dcb39e3f54564d47763a6ad7abf170`. Baseline JSONL SHA256 `f497948e2d45e793b612b43265ef5b12d81479695a7b27cf7ba733e3d12573f2`; mutation SHA256 `355ee8008035a14f682b2c31fc2bf371b6b87f2164e02445257cac728e8b0163`. Runner SHA256 `b304ee2b31a6882235911af15390534a79850cd3cc31850931744b6bc037ef54`.

**U:** The source data and known synthetic generator bound this result to audit integrity only. It says nothing about real GUI failures, population exchangeability, estimator accuracy in deployment, or safety. No GPU was useful for this deterministic 204-row check.

## Reproduction

The immutable raw archive is already stored in main at `research/analysis/unseen_failure_mode_yield_5665_t1_v2/results/t1-host-02/raw-jsonl-gzip-b64/`. Copy its 18 `part-NN.b64` files into `/transport`, and use the archived v2 `RAW_MANIFEST.json` plus this package's `prepare.py` to reconstruct `/input/base.jsonl` and `/input/mutated.jsonl`. The preparation validates the archive's gzip/base64/raw hashes and the one-record mutation. The audit copy is byte-identical to the frozen v2 audit.

Preflight without target invocation:

```sh
python -B runner.py --validate-inputs
```

Formal invocation (mount package source read-only, `/input` read-only, `/output` writable):

```sh
python -B runner.py
```

The formal runner calls `audit.py` exactly twice, once for each input, and writes the captured outputs and `result.json` under `/output`.

## Corrective implication

The v2 audit should report both scheduled IID count and independently recomputed eligible IID count. Its PASS condition must require the eligible count to equal the frozen 200-row denominator; a HOLD row must cause the all-200 requirement to fail. The display field named `eligible_iid_rows` must not equal the scheduled IID list length when some rows were skipped. Implement and validate that as a separately reviewed successor; do not edit historical v2 results in place.

## Formal evidence

- Result JSON SHA256: `1d42e3d342cb6599b4afc174c8af6ddd438bd9981666a09151cab544bbcb80e3`.
- Baseline stdout SHA256: `13d93ec8fce04c115965fc7100e643023bf80c4186a80af0169e13e7239d8586`.
- Mutated stdout SHA256: `04d0920124429c8d977b7804bb42c2473ffa4e7287fbb61e39168c5b3a3e0538`.
- Both stderr files are empty (SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).
- Frozen allocation, A01 stop and A02 outcome are append-only comments on [Issue #5665](https://github.com/Unjuno/agent-interface/issues/5665).
