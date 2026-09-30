# Independent local raw recheck — Issue #5315

## Disposition

`PASS_INDEPENDENT_RAW_RECHECK` for the already executed immutable synthetic finite-sample unit. This is a supplemental CPU audit, not a new formal experiment or a rerun. Preserve the existing issue-level `HOLD_UNVERIFIED_FULL_RISK_CONTRACT`, the audit-v1 failure, and all original allocations unchanged.

## Inputs and reproducibility

- Raw URL is pinned in `audit_local_independent_stream.py` to source commit `e30ed8d5cf4b3e4846f6f8afc3c5b59e57d3dbc3`.
- Raw SHA-256: `4ead9d0a552db86332a4c8ac08b9f6e01fcc1f6066e645ae15ead9c9395c8b37`.
- Receipt SHA-256: `6401627c5777b6ee42a5ce7fd26457d2355854fc53095be4cd35d4750ce6a55a`.
- Audit source SHA-256 (UTF-8, LF): `a6da8e2a49073f44e57cc208c7c3b0985f2c25e40e4b10e9fa105a23e6b112ce`.
- Runtime: CPython 3.11.9 on the local Windows host; standard library only. The audit streams from immutable raw URLs and does not save the 23 MB raw or receipt locally.
- Command: `python -B research/analysis/conformal_verifier_risk_contract_5315_v1/audit_local_independent_stream.py`.

## Checks and result

The independent implementation verifies input hashes, every JSONL row's ranks/cutoffs/decision set and outcome fields, trial order and denominators, reconstructed receipt aggregates, analytic finite-sample inclusion values within absolute 0.015, the n=4 unattainable-rank full-set/no-singleton boundary, and the known-shift full-set override. Three corruption controls (outcome flip, cutoff mutation, invalid calibration value) were each rejected.

Observed: 20,000 rows (10,000 each for n=4 and n=10); zero row/reconstruction errors. At n=10, IID conformal inclusion was 0.9025 (oracle 0.9091) and shifted inclusion was 0.8261 (oracle 0.8333). At n=4, conformal returned full sets (mean size 2, singleton rate 0). All three mutations were rejected.

## Scope

This checks the exact synthetic raw artifact only. It provides no evidence about real verifier accuracy, task populations, an operational shift detector, adaptive-query exchangeability, external effects, authority, or product safety. No model, GPU, CUDA, Docker, or formal allocation was involved.
