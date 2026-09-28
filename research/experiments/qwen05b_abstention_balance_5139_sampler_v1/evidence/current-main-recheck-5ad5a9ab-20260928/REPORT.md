# #5139 current-main construction compatibility recheck

## H / T / D / C / U

- **H:** The additive #5139 support sampler/auditor and its two deterministic synthetic construction probes remain executable and preserve their retained results on current main `5ad5a9ab465e2b0052aa301b1909b92816e70025`.
- **T:** In the isolated #5208 branch, fetched and merged current `origin/main` at the exact SHA above. The common ancestor was `71f85380669795d21c668bcbc832ae896d0b6220`. A path-level three-way change-set audit found 54 main-changed paths, 30 branch-changed paths, and zero overlapping paths. Ran the complete host package suite and both probe entrypoints directly from repository root; compared each parsed JSON result to its previously retained `result.json`.
- **D:** CPython 3.11.9 host suite: **27/27 passed** in 1.379 seconds. Feature-marginal probe: **128/128** support-seed sentinels, `PASS_STRATIFIED_SUPPORT_MARGINAL_FEASIBILITY_ONLY`; joint-cell probe: **128/128**, `PASS_JOINT_AND_MARGINAL_MATCHED_SET_FEASIBILITY_ONLY`. Both parsed outputs exactly match retained JSON (`feature_result_match=True`, `joint_result_match=True`). Direct stdout is retained beside this report; stderr was empty for both probes. The probes use only their pre-existing synthetic sentinel fixtures, not a formal allocation.
- **C:** One Windows host, CPython 3.11.9, no container, Docker/OrbStack, CUDA/GPU, model/checkpoint, fit, adapter write, or formal seed. Probe source Git blobs remain feature `aa13a75607c9a6dad4a95b301c9d4c202e417b98` and joint `518e43988d89c46764e4bab61920311765791db6`; the main merge did not change either package path. This is host construction/reproducibility evidence only.
- **U:** Does not test or claim model efficacy, quality, safety, GPU behavior, pinned-container execution, or formal allocation outcomes. The identical result JSON is reproducibility, not new independent scientific evidence. It does not resolve the historic `sad_cannon` attribution or grant any GPU/Docker lease. Formal #5139 remains gated on fresh source/data/model/tokenizer/image freeze, predecessor disposition, collision checks, and exact coordinator authorization.

## Exact commands and retained output

```text
python -m unittest discover -s research/experiments/qwen05b_abstention_balance_5139_sampler_v1 -p 'test_*.py' -v
Ran 27 tests in 1.379s — OK

python research/experiments/qwen05b_abstention_balance_5139_sampler_v1/evidence/feature-marginals-128-20260928/feature_design_probe.py
python research/experiments/qwen05b_abstention_balance_5139_sampler_v1/evidence/joint-cell-marginals-128-20260928/joint_matched_feature_probe.py
```

Each stdout JSON file is the exact direct entrypoint output. The original probe source and retained result files are not modified.

## STOP and resource-governance disclosure

No Docker command was used for this recheck. Separately, Issue #5085 comment #5864462673 discloses three earlier unauthorized local Docker starts from this continuing task; they are preserved as a governance violation, not a result or lease. No further Docker/GPU operation is made here. The 5139 GPU/Docker formal authorization remains absent.
