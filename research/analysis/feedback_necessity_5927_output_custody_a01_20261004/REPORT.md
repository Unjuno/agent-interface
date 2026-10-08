# Issue #5927 output-custody successor A01

**Disposition: `PASS_CONSTRUCTION_ONLY`.** The successor candidate and raw-only auditor refuse an existing `--out` path without changing its bytes, and both still write successfully to a fresh path. The original frozen T0 package and its formal result remain unchanged.

## H / T / D / C / U

- **H:** The frozen T0 candidate and auditor overwrite an existing output path with `Path.write_text`. Exclusive creation should fail closed on a collision while preserving the first file.
- **T:** A copied, source-derived successor CLI runs the same two finite fixture cases. Construction tests pre-create sentinel files at candidate and audit output paths and exercise each real `main` entry point. A fresh-path CLI smoke check verifies the normal write path.
- **D:** The first test run failed exactly the two new custody checks: neither CLI raised `SystemExit` on a collision. After switching both writers to exclusive file creation, all nine tests passed. A fresh-path CLI smoke check wrote two candidate rows and an auditor result of `PASS_RAW_AUDIT` with zero errors.
- **C:** Tests use local temporary files and authored finite cases. The host filesystem's exclusive-create semantics are the boundary under test; no concurrent-process stress or cross-filesystem behavior was measured.
- **U:** This is a CLI construction check only. It does not repeat or alter the consumed T0 allocation, establish runtime or application behavior, or change the T0 `PASS_METHOD_SCOPED` result. Callers must use these successor entry points to receive the write-once behavior; the historical frozen scripts remain byte-for-byte unchanged.

## Provenance and verification

The source baseline is `f2aa59c8bac88f0091eb24c4f462f55a72303d2f`. The copied computation and input originate from `research/analysis/feedback_necessity_5927_epistemic_controls_t0_20261002/`; that package's `FREEZE.json` source hashes were independently checked against the repository blobs. No OrbStack, WSLc, GUI, model, or formal candidate/auditor allocation was used for A01.

Construction test command:

```text
python -B -m unittest discover -s research/analysis/feedback_necessity_5927_output_custody_a01_20261004 -p test_method.py -v
```

Result: 9 tests passed, including the seven inherited finite-method controls and two output-collision regressions. `construction.stdout.txt` retains the successful test output; `SHA256SUMS` binds this successor's source, cases, report, and test log.
