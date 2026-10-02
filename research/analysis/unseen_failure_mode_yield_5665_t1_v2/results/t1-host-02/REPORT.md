# Issue #5665 T1 — unseen failure-mode method construction

**Disposition: METHOD_PASS and METHOD_COMPARISON_PASS_SCOPED.** The independent raw-only audit passed. This is synthetic method evidence only; it does not establish repository failure coverage, safety, or saturation.

## H / T / D / C / U

- **H:** In this fixed IID categorical generator, singleton mass f1/n predicts future unseen-class encounter better than the trailing-K=20 novelty baseline.
- **T:** 200 independent replicates; each contains 100 conditional-on-failure training draws and 500 held-out draws from F0–F7 with weights [500,250,120,60,30,20,10,10]. Four extra records exercise correlated duplicates, taxonomy version drift, distribution shift, and a missing training outcome.
- **D:** The raw audit replayed all 200 eligible IID rows and all four holds with zero errors. All four mutation controls were detected. Mean absolute error was lower for f1/n than the trailing-K baseline against exact unseen mass (0.01335 vs 0.02105) and the held-out new-mode rate (0.01374 vs 0.02126). Thus the preregistered T1 method and fixed-generator comparison criteria passed.
- **C:** The result supports only the stated independent-draw distribution. A recency method may do better when discoveries are clustered; taxonomy coarsening or a changed distribution can mimic saturation.
- **U:** Every training draw represents a failure class. This is conditional-on-failure class mass; no per-trial failure probability was sampled. No inference follows about real task reliability, population-wide failure modes, or catastrophic risk. Synthetic labels, known class weights and independent draws omit adaptive search, real adjudication, censored outcomes and evolving versions. T1 is not H_PASS_SCOPED.

## Reproduction and provenance

Allocation: `issue5665-failure-mode-yield-t1-20261001-02`; base main: `3ed5d7865daaaf202c59054c3545ade968446fc8`. Frozen runner SHA-256 `8ecfa3b3fd6009de70c5ba3854b8cf9f8c927d8a719f73cf9150c3e9d932d3c2`; independent auditor SHA-256 `cefb6efa1b7c67f6a6eca46e732dae9e564de9fbd698acccd5a407949a3ae6dd`.

Runner was invoked once (exit 0): `python run.py --out results/t1-host-02/raw.jsonl`. The independent auditor was invoked once (exit 0): `python audit.py results/t1-host-02/raw.jsonl`. CPython 3.11.9 on Windows 10 host CPU. Docker/OrbStack was unassigned, so this did not run in a container; no GPU, model, network, GUI, real task input, or external effect was used.

The raw JSONL is 4,304,789 bytes with SHA-256 `f497948e2d45e793b612b43265ef5b12d81479695a7b27cf7ba733e3d12573f2`. It is preserved as ordered Base64 chunks of one gzip stream because the GitHub contents API does not accept this raw payload as a single text call. Concatenate `raw-jsonl-gzip-b64/part-00.b64` through `part-17.b64` without separators, Base64-decode, then gzip-decompress. The decoded byte stream must have the raw size and SHA above. The reconstructed local bytes matched exactly. See `RAW_MANIFEST.json` for transport hashes and commands.
