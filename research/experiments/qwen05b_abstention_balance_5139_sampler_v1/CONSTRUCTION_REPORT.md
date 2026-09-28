# Issue #5139 sampler construction-only record

## Scope and status

This is a host-CPU-only construction check for the pre-formal sampler correction in Issue #5139. It is not a model training run, data-quality result, Docker experiment, or GPU result. The sampling correction addresses the immutable v2 deterministic-prefix confound without changing any #4988/#5014 source, seed, dataset, output, or verdict.

Frozen base for this additive sampler bundle: `main` SHA `3007e03481d545eb9a92b8cec07c8c4201bd3728`. Branch: `research/qwen05b-abstention-balance-5139-sampler-20260928`. Study path: `research/experiments/qwen05b_abstention_balance_5139_sampler_v1/`.

## H / T / D / C / U

- **H (narrow construction claim):** SHA-256 class-conditional ranking gives deterministic row-order-independent support lists; selecting both arms from the same per-class ranked list yields nested selections and identical rows for classes with equal counts. This does not test the #5139 efficacy hypothesis.
- **T:** Four host unit tests over a synthetic 128-row support-pool shape matching the inspected v2 class/template index schedule. Rank key is UTF-8 `support-row-rank-v1\n{seed}\n{class}\n{case_id}`; order is ascending by (digest bytes, case_id UTF-8 bytes). Probe seed string `construction-only-manual-probe` is not an allocation seed and must not be reused for construction/formal allocation.
- **D:** `PASS_SAMPLER_CONSTRUCTION_ONLY`: 4/4 tests passed. The old first-four `set` prefix covers one template; the ranked four-row set sample for this probe covers all four. Both support arms cover all four set templates. Every class selection is nested in the larger arm, and equal-count classes receive identical ordered rows. Duplicate IDs and a short/missing class fail closed.
- **C:** Python 3.11.9 host process; deterministic synthetic row metadata; no model, tokenizer, package install, network data, GPU, CUDA, container, GUI, or input. The test does not import the v2 protocol or model output.
- **U:** This validates only sampler mechanics on a synthetic row-shape fixture. It is not an independent raw-data auditor, not a pinned-image construction gate, not a test of the full current-main dataset generator, and not evidence of LoRA quality, safety, speed, or population generality.

## Exact command and outcomes

Passed command:

```text
python -m unittest discover -s research -p 'test_qwen5139_sampler.py' -v
```

Result: 4 tests, 0.002 seconds, exit 0.

Two harness/checker mistakes were retained rather than silently omitted:

1. The first exploratory PowerShell checker asserted that the imbalanced arm always has at least as many rows as the balanced arm. That assertion failed for the four YIELD classes (counts 1 vs 4); the allocation design intentionally reverses subset size there. After checking inclusion from the smaller selected set into the larger one in either direction, the construction diagnostics were: `nested_all_classes=true`, `same_rows_where_counts_match=true`, `unique_support_ids=true`, old set-prefix template count 1, ranked balanced set template count 4, ranked imbalanced set template count 4.
2. The first unittest invocation used module-name loading from the workspace root and failed before discovery with `ModuleNotFoundError: No module named 'test_qwen5139_sampler'`. The correct explicit discovery command above ran the same tests successfully.

Source SHA-256 values from the local tested files:

- `sampler.py`: `80eb3663e0215142104719882ca9640df37e88345d3d7945979bff45fd7ae907`
- `test_sampler.py`: `74378868d5f43c137b96ac9e5b47fc23ae5ae57c1da223beb7927e86bdaaf79b`

## Resource / allocation boundary

The current #5085 comments return the #5133 CPU-only slot after its construction STOP. That return does not assign a GPU/Docker lease to #5139. No #5139 allocation seed, model load, CUDA call, fit, adapter write, Docker invocation, or formal output was consumed here. Keep the branch preparatory; do not merge it as a completed experiment. A full fresh-main source/data/model freeze, independently implemented raw auditor, pinned-image CPU gate, historical `sad_cannon` attribution disposition, output/seed collision check, and explicit named #5139 GPU/Docker lease remain required before any model or container work.
