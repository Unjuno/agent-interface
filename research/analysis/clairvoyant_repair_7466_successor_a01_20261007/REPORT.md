# Issue #8283 result — corrected #7466 hindsight diagnostic

## Disposition

**PASS_DIAGNOSTIC_REPAIR within the frozen synthetic A03 dataset.** The corrected comparator produces finite, strictly positive costs for all 432 retained episode×cost rows, and every candidate-minus-oracle gap is nonnegative. All 18 cohort×checkpoint/replay-cost cells contain 24 rows. This repairs only the withdrawn diagnostic; it does not change A03's formal FAIL_UNSAFE_RESUME, explain that failure, or establish adaptive efficacy.

## Identity and reconstruction

- A03 frozen sources: 6/6 SHA-256 values match FREEZE.json.
- A03 frozen inputs: 3/3 SHA-256 values match FREEZE.json.
- Compressed candidate: 18,362,497 bytes; SHA-256 b391bc0edb3799a6ad0badf7b9f2abe23457b55d13277dc51b477b7abdd6cdb7.
- Decompressed raw candidate SHA-256: afaf783f1f8f8e5f7c4ee93661e27f8962a0c883456650531278de901bd3135f; checked as a streaming hash without materializing the 314,596,618-byte raw file.
- Retained candidate-source receipt matched frozen candidate.py; receipt and streamed array both report 432 rows.
- Corrected DP independently evaluated all 432 rows; the lossless gzip was decoded as a stream, reading only the episodes array and not materializing the large transcript.
- Candidate invocations added: 0. Frozen-auditor invocations added: 0. A03 source, result, and disposition unchanged.

Four boundary fixtures passed: no interruption has zero optimal checkpoint/replay cost; one interruption incurs one replay unit; two interruptions incur two replay units; and a checkpoint is not available at an illegal boundary. Local unit tests: 4/4.

## Cell summaries

Values below are median corrected oracle cost / median candidate-minus-oracle gap; each cell has n=24.

| Cohort | Checkpoint/replay 1/1 | 1/3 | 4/1 | 4/3 | 8/1 | 8/3 |
|---|---:|---:|---:|---:|---:|---:|
| Informative | 50.5 / 141.5 | 115 / 386 | 101.5 / 259 | 169 / 446 | 167 / 786 | 238 / 668 |
| Independent | 70 / 690.5 | 158.5 / 2112.5 | 142 / 661.5 | 235 / 2059 | 225.5 / 641.5 | 333 / 2012 |
| Reversed | 201 / 2755.5 | 470 / 8402.5 | 367 / 2590.5 | 657.5 / 8203.5 | 552 / 2416.5 | 890.5 / 7976 |

All per-row and per-cell values are in RESULT.json.

## Execution note and local validation

The full computation wrote RESULT.json successfully, then the CLI exited 1 because its final summary-print list used a nonexistent result-key name. The stored data and gates were read back and verified; the print-only key typo was corrected in source afterward. The write-once result was not rerun or rewritten. Therefore the calculation artifact is complete, but the original computation command's final process exit was not zero; this is reported rather than hidden.

Post-run checks on the saved evidence and current source:

- unittest discovery: PASS, 4/4.
- py_compile: PASS.
- analysis index strict check: PASS, 761 retained directories indexed before adding this package.
- git diff --check: PASS.

## Limits

The repaired oracle is a hindsight optimum over a synthetic trace and stipulated costs. It is not an executable policy, and the candidate cannot observe its future labels. It does not establish realism, semantic checkpoint persistence, exact real effects, interruption predictability, production safety, GUI behavior, latency, or benefit. The original A03 failure remains unchanged.
