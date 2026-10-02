# Needle #5139 stratified-support feasibility probe

## H / T / D / C / U

**H — narrow feasibility hypothesis.** On the support-pool shape implied by the immutable #5014 protocol, a deterministic class-conditional selector can choose the 16-row and 4-row `set` subsets so both have exactly the same template and field *marginals*, while the 4-row subset remains nested in the 16-row subset.

**T — construction probe.** Reconstructed 64 `set`-class metadata rows from the 128-row support schedule in `protocol.py` (`i % 8 <= 3`; template `(i // 8) % 4`; field `FIELDS[((i // 8) + (i % 8)) % 4]`). The referenced source is the immutable #5014 branch blob `d5073b51d38fb9f649ed799eafcaa5e0eda5fc18`, read during GitHub intake. A fixed construction-only sentinel `construction-feasibility-sentinel-20260928` ranks one row in every template×field cell for the 16-row arm; a deterministic bijection selects one field per template, covering all four fields, for the nested 4-row arm. This sentinel is not an allocation/formal seed and was not selected for model outcomes. No model, optimizer, task execution, or GUI was involved.

**D — result.** `PASS_STRATIFIED_SUPPORT_FEASIBILITY_ONLY`. Pool: 64 rows, four candidate rows in each of 16 template×field cells. 16-row arm: 4/template and 4/field. 4-row arm: 1/template and 1/field. The small arm is a subset of the large arm. The independent raw-only auditor returned `errors=[]`; four host unit tests passed, including mutation checks for non-nesting, changed marginals, and duplicate IDs.

**C — controls.** Both arms share one reconstructed pool and identical generation rules; selected rows are drawn from the actual synthetic pool. A fixed sentinel plus hash ranking gives deterministic choices. The audit module does not import the builder. Exact support class counts are 16 versus 4 as in the predecessor-shaped `set` stratum; the remaining support classes and held-out rows are outside this probe.

**U — limits.** This is a host-only construction feasibility probe on synthetic row metadata, not the complete #5139 dataset generator, not the pinned-container CPU gate, not a raw-output/model audit, and not a GPU/Docker/LoRA experiment. Matching marginals does not match the joint template×field distribution: the larger arm spans 16 cells and the smaller arm 4 cells. It does not establish that this constrained design is the best preregistration, that exact same joint composition is possible at 4 rows, or any model efficacy, safety, latency, generalization, or causal quality effect. Do not use this sentinel for a formal allocation or select a formal seed by observed coverage/outcome.

## Provenance and execution

- GitHub `main` observed at intake: `8346f25ba07695c0bd554bfee7d335295c9a323d`.
- Protocol source blob: `d5073b51d38fb9f649ed799eafcaa5e0eda5fc18` (retrieved from the #5014 branch; main does not contain that old experiment path).
- Host: Windows PowerShell, Python 3.11.9. No packages installed and no network used by the probe.
- Commands:

  ```powershell
  python -m unittest discover -s scratch/needle-stratified-feasibility -p 'test_*.py' -v
  python scratch/needle-stratified-feasibility/build_support.py scratch/needle-stratified-feasibility/raw.json
  python scratch/needle-stratified-feasibility/audit_support.py scratch/needle-stratified-feasibility/raw.json
  ```

- Results: 4 tests passed (0.001 s on final run); runner exited 0; separate auditor exited 0 with `{"errors":[],"verdict":"PASS_STRATIFIED_SUPPORT_FEASIBILITY_ONLY"}`.
- Source SHA-256: `build_support.py` `72f22a12665fa1e75da166ea18a45b10d69b45215e22546e483e647451846786`; `audit_support.py` `b45b2880ccff0e3b945b8702ed6451ab8483e7a5f784ae9efd69a3014498534e`; `test_support.py` `10b6eb386b6a5d99afc5b1f3da81ad22f7803224d2bafb74ed8c42161a33c01b`.
- Raw output: 7,105 bytes, SHA-256 `361a17ee45c6dd6e2e69b89da3c93216d4d2d778b95d4afdfbb68b4a98308053`.
- Docker Desktop `desktop-linux` responded at client/server 29.8.0 and the cached CPU image `needle-pilot05:local` was verified as `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e` (`linux/amd64`); neither Docker invocation nor image execution occurred. The #5085 queue has no lease for this allocation and forbids inheriting a sibling's slot. This is deliberately a host-only feasibility probe, not a Docker result.

## Follow-up implication for #5139

This supports a possible allocation-independent stratified sampler that freezes a seed before outcomes, balances template and field marginals in the `set` class, reports the residual joint-cell imbalance, and preserves the 32-row per-arm budget and shared held-out set. Before any formal study, implement/review the design against the full current-main generator and independent auditor in a fresh additive freeze; do not modify #5014 bytes or the existing #5139 sampler branch, do not choose a seed after inspecting coverage or model outcomes, and do not run GPU/Docker work without a new exact #5085 lease and disposition of the unresolved `sad_cannon` attribution.
