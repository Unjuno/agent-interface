# Issue #5665 audit eligibility gate correction (A03)

## Outcome

A03 verifies an additive correction to the frozen #5665 T1 raw-only audit. The v2 audit accepted a nonexchangeable IID row while reporting 200 eligible; its decision field independently showed 199. A03's corrected audit requires all 200 preregistered IID records to remain eligible and reports scheduled and eligible counts separately.

One clean baseline passed at 200/200. Four single-record mutations (nonexchangeable stratum, invalid denominator, taxonomy drift, duplicate unit ID) each failed closed at 199 eligible IID records. The independent raw-only reviewer matched all five expected decisions. One WSLc container launch, five corrected-audit invocations, retries 0. Full frozen details and links are in `FROZEN.json` and the append-only [Issue #5665 record](https://github.com/Unjuno/agent-interface/issues/5665).

This is a method-integrity result on a known synthetic dataset. It does not retest the candidate estimator, generalize to real failures, or establish safety or deployed predictive value. Historical v2 results remain untouched.

## H / T / D / C / U

**H:** Adding a fixed-denominator eligibility gate and distinct scheduled/eligible counts closes the A02 false-accept while retaining a clean baseline PASS.

**T:** Use the frozen 204-row baseline, then run the corrected audit once on baseline and four one-record mutations for nonexchangeability, denominator inconsistency, taxonomy drift, and duplicated unit identity. Independently classify eligibility from raw row fields.

**D:** Baseline must return exit 0 / PASS with scheduled=200 and eligible=200. Every mutation must return exit 1 / FAIL, scheduled=200, independently eligible=199, decision replicates=199, and an explicit `iid_eligibility_count:199` error. Independent review must accept all five preregistered outcomes. Result: PASS_CORRECTED_GATE, 5/5.

**C:** The historical v2 source is preserved as `audit_v2_frozen.py` (Git blob `c8de1110855c0886b142ec0400677120b9f6a216`, SHA256 in FROZEN.json). The corrected candidate is an additive copy. Frozen image: `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, WSLc 3.0.1.0, Python 3.12.15, network none, CPU 1, source and cases read-only, output writable.

**U:** This verifies only the stated audit-gate behavior on the retained synthetic cohort. No GUI, model, live game, physical input, estimator generalization, or safety property is tested. GPU is unnecessary for deterministic 204-row validation.

## Reproduction

The immutable raw transport remains in main at `research/analysis/unseen_failure_mode_yield_5665_t1_v2/results/t1-host-02/raw-jsonl-gzip-b64/`. `RAW_MANIFEST.json` and `reconstruct_raw.py` validate/decompress its 18 chunks and emit `/input/base.jsonl` (plus the historical A02 mutation). Copy the exact baseline into the source mount as `/src/base.jsonl`. Then run `prepare_cases.py` in a network-disabled container with `/src` read-only, `/cases` writable; it writes the four one-record mutation JSONL files and `PREPARED.json`. Use the expected file hashes in `cases-manifest.json` to verify them.

Run `runner.py --validate-inputs` before the formal command. It checks source/case hashes, row identity and mutation scope, independently recomputes eligibility, compiles the candidate in memory, verifies `/output` is writable, and invokes the target audit zero times.

The formal command is one WSLc container with source and `/cases` mounted read-only and `/output` writable:

```sh
python -B runner.py
```

It invokes `audit_v3_candidate.py` exactly five times and writes exact stdout/stderr plus `result.json`. Never use it to rerun A03; create a separately frozen successor for any future validation.

## Corrective diff

Compared with the frozen v2 audit, A03 adds one required-count error when recomputed eligible IID rows are not exactly 200, returns `eligible_iid_rows` from the recomputed eligible list, and adds `scheduled_iid_rows` for the full schedule count. No metric formula, raw result, or historical file is changed.

