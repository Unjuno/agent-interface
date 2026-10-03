# Core boundary conjunction: scoped integration evidence for #57

Three existing candidate fixes compose in the declared inert bridge:
**PASS_CORE_BOUNDARY_CONJUNCTION_SCOPED**. The original runtime source is not
changed by this evidence package. It compares exact current-main core bytes
with the executable-source conjunction of PRs #6860, #6863 and #6866.

| Retained check | Baseline | Combined |
|---|---:|---:|
| Distinct finite input rows | 3,072 | 3,072 |
| Rows inconsistent with the typed reference contract | 2,164 | 0 |
| Inert execute callback entries | 135 | 2 |
| Callback entries outside the declared valid-input gate | 133 | 0 |
| Synthetic method completions | 135 | 2 |

The mismatch denominator includes leaked TypeError and changed refusal results;
it is not a count of physical unsafe operations or an estimated failure rate.
Two combined positive controls cover core time zero and exact expiry equality.
Seven independent guard deletions and seven copied-raw corruptions are all
detected. Combined regression suite: 84 tests normally, 84 with `-O`; doctor
exit 0. All original baseline/combined rows, nine compressed deletion-control
raw files, exact source bytes, command/exit receipts and the first control
wrapper failure are retained.

See [PLAN.md](PLAN.md) for prospective H/T/D/C/U and [REPORT.md](REPORT.md) for
provenance, results, failure preservation and limitations. `FREEZE.json` pins
the original 42 files; `CONTROL_FREEZE_V2.json` pins the newline-aware wrapper
repair. [SOURCE.json](SOURCE.json) binds candidate heads, base and patches.

From this directory, verify all retained bytes and reconstruct the audits:

```sh
python -B verify.py
```

To reproduce the finite checks without overwriting retained results:

```sh
python -B runner.py --arm baseline --output /owned/new/baseline.jsonl
python -B runner.py --arm combined --output /owned/new/combined.jsonl
python -B auditor.py --arm baseline --raw /owned/new/baseline.jsonl
python -B auditor.py --arm combined --raw /owned/new/combined.jsonl
python -B controls_v2.py --scratch /owned/new/deletions --output /owned/new/controls.json
```

The controls require the retained combined raw and an absent owned scratch
directory. They use explicit inert adapters and sequential native Python only.
Fresh reproduction is an ordinary engineering check, not a new live/formal
allocation. Do not replace the retained first outputs with reproduction.

For combined regressions, change to `source/combined` and run:

```sh
python -B -m unittest discover -s runtime/core_v1 -p 'test_*.py' -v
python -O -B -m unittest discover -s runtime/core_v1 -p 'test_*.py' -v
python -B -m runtime.core_v1.doctor
```

Scope: actual deterministic core and compiled runtime functions, authored
synthetic observations and an inert glue adapter. No public native-adapter,
OS input, physical release, independent application effect, scheduler,
common-clock trust, model, container, GPU or efficiency claim. Source
conjunction is not a complete-PR merge candidate or conditional-main apply
verification. Original per-PR committees/reviews and FINAL-v5 gates remain.
