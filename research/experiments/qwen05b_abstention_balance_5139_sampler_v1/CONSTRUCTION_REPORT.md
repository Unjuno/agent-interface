# Issue #5139 sampler construction-only record

## Scope and status

This is a host-CPU-only construction check for the pre-formal sampler correction in Issue #5139. It is not a model training run, data-quality result, Docker experiment, or GPU result. The sampling correction addresses the immutable v2 deterministic-prefix confound without changing any #4988/#5014 source, seed, dataset, output, or verdict.

The first publication branch used base `3007e03481d545eb9a92b8cec07c8c4201bd3728`, and the second used `a78dfcfcc0ffdd1864abd9170087e835b5467f91`; both became stale as main advanced. Review branch `research/qwen05b-abstention-balance-5139-sampler-v3-20260928` is based on `faf30993f987b2a4ea1e6f85d322ab6c91ab1b7c`; main later advanced to `716d25286ec37999d8098cd63bf1731fae0d88d6`, so this preparation branch is stale and is not formal-run-ready. The sampler itself remains unchanged. This report now includes a separately implemented support-selection auditor and its host mutation tests. Study path: `research/experiments/qwen05b_abstention_balance_5139_sampler_v1/`.

## H / T / D / C / U

- **H (narrow construction claim):** SHA-256 class-conditional ranking gives deterministic, input-order-independent row order; selecting both arms from the same per-class ranked list yields nested selections and identical rows for classes with equal counts. This does not test the #5139 efficacy hypothesis.
- **T:** Six host unit tests over a synthetic 128-row support-pool shape matching the inspected v2 class/template index schedule. Rank bytes are SHA-256 of UTF-8 `support-row-rank-v1\n`, followed by the positive seed as canonical ASCII decimal (no sign or leading zeros), then UTF-8 class name and case ID, newline-separated. Sort by `(digest bytes, case_id UTF-8 bytes)`. The test-only integer seed 1 is not an allocation seed and must not be reused for a construction/formal allocation.
- **D:** `PASS_SAMPLER_CONSTRUCTION_ONLY`: 6/6 unit tests passed. The separate deterministic construction descriptor for test seed 1 showed old `set` prefix template count 1; ranked balanced per-template counts `{0:1, 1:1, 2:2, 3:0}`; ranked imbalanced counts `{0:3, 1:3, 2:6, 3:4}`. This demonstrates that hashing removes deterministic row-prefix selection but does **not** guarantee matched template/field coverage. Counts are reported, not used to select or replace the seed. Both arms are nested in either count direction; equal-count classes have identical ordered IDs; duplicate IDs, missing/short classes, and noncanonical seeds fail closed.
- **C:** Python 3.11.9 host process; deterministic synthetic row metadata; no model, tokenizer, package install, network data, GPU, CUDA, container, GUI, or input. A separate test-oracle function reconstructs ranked IDs without importing the candidate `row_rank` or sampler. This is not a separately executed raw-output auditor or independent human review.
- **U:** This validates only sampler mechanics on a synthetic row-shape fixture. It is not a pinned-image construction gate, not a test of the full current-main dataset generator, and not evidence of LoRA quality, safety, speed, or population generality.

## Candidate sampler command and outcome

Passed command:

```text
python -m unittest discover -s research/experiments/qwen05b_abstention_balance_5139_sampler_v1 -p 'test_sampler.py' -v
```

Result: 6 tests, 0.002 seconds, exit 0.

## Independent support-selection audit — host CPU only

`audit_sampler.py` is stdlib-only and does not import the candidate sampler or protocol. Given a dataset-shaped object, it independently computes the prescribed SHA-256 ranks from `support_seed`/class/case ID, reconstructs the exact per-arm selected IDs/order from `support_pool`, checks class counts, and compares complete selected rows. It does not use the separate formal/training `seed`. The standalone audit fixture tests different formal and support seeds; its selected rows are built with a separate test-side SHA-256 implementation, and it imports neither the candidate sampler nor its test module, so this PR is independently runnable.

Passed commands:

```text
python -m unittest discover -s research/experiments/qwen05b_abstention_balance_5139_sampler_v1 -p 'test_audit_sampler.py' -v
python -m unittest discover -s research/experiments/qwen05b_abstention_balance_5139_sampler_v1 -p 'test_*.py' -v
```

Audit tests: 7/7; complete package tests: 13/13; exit 0. Five evidence mutations were rejected: changed support seed, reversed arm order, substituted row, mutated selected-row field, and duplicate pool ID. An additional control changed only the formal seed and was correctly accepted as irrelevant to support ordering. The positive check reconstructed both arms from the synthetic 128-row pool. Test-only support seed 1 and synthetic formal-seed sentinel 900000001 are fixture values only; neither is an allocation seed or reused study seed.

This is not the independent raw-output audit of a formal dataset or training result. It does not execute the full #5139 data generator, a pinned container, model/tokenizer, CUDA, or LoRA fit.

## Preserved construction/checker failures

1. The first exploratory PowerShell checker asserted the imbalanced arm always had at least as many rows as the balanced arm. That check failed for the four YIELD classes (counts 1 vs 4); the design intentionally reverses subset size there. A corrected inclusion check tested that the smaller selected set is contained in the larger one in either direction.
2. The first unittest invocation used module-name loading from the workspace root and failed before discovery with `ModuleNotFoundError: No module named 'test_qwen5139_sampler'`.
3. A later test asserted that a four-row hash-ranked `set` sample must cover all four templates. Under canonical integer test seed 0, the sample covered only two templates. That assertion was rejected as an unsupported invariant; no template-coverage constraint or seed search was added. Test seed 1 is used only as a fixed mechanics sentinel, and its realized template/field counts are reported above.
4. Running `unittest discover -s research` while already in the `research/` directory failed before test discovery (`Start directory is not importable: 'research'`). The exact root-relative command above then passed 6/6.

## Local source SHA-256

- `sampler.py`: `0cdbe3e5b61202ec6ea5bd8810f4734a85141e7a7cbaf22ce886568b0f2c23a6`
- `test_sampler.py`: `e0fbcf0a3c1cce969e3f6751da8d56d952ce3002d46db19f5e3f40b97e4dacbe`
- `audit_sampler.py`: `26007eee3d9402842953618fc2225c200b2f3ad8ab61d49be93840fd84e68638`
- `test_audit_sampler.py`: `99f974805c94a90589bf3ff826195023e6d4e48cbfcec6c47400480db9b21672`

## Resource / allocation boundary

Current #5085 arbitration assigns the exact serialized CPU-only OrbStack slot `needle-publication-orbstack-bind-5066-20260928-02` to #5134, frozen at main `716d25286ec37999d8098cd63bf1731fae0d88d6`; it explicitly excludes every other container lane, including #5139. This is not a #5139 GPU lease. No #5139 model load, CUDA call, fit, adapter write, Docker invocation, or formal output was consumed here. Keep this PR preparatory; do not merge it as a completed experiment. A full fresh-main source/data/model freeze, independent raw-output auditor (the new host sampler auditor does not satisfy it), pinned-image CPU gate, historical `sad_cannon` attribution disposition, output/seed collision check, and explicit named #5139 GPU/Docker lease remain required before any model or container work.

