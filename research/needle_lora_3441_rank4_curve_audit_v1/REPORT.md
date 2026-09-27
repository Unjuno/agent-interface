# Successor #3865 — independent CPU audit of #3851 curves

Status: **PASS_CURVE_ONLY_AUDIT_SCOPED**. Exact predecessor artifact was audited once on CPU; no training/CUDA.

Construction suite: 6/6 checks passed before freeze. The first #3865 auditor invocation is preserved as a setup STOP caused by case-sensitive digest comparison; this #3875 successor normalized comparisons and tested both cases before its one formal offline audit.

This additive block performs offline, CPU-only audit of the immutable #3851 raw stdout. It does not train or call CUDA. The #3851 formal invocation is consumed and remains an audit STOP: the frozen runner scored final predictions after its rollback helper reset the live adapter. #3865's single CPU audit also stopped before payload processing because the SHA comparison was case-sensitive; its empty stdout capture and predecessor freeze are preserved under renamed files. This block audits only the 16 retained pre-rollback learning curves and never uses those invalid post-rollback final scores.

The exact input is copied as `predecessor_raw_stdout.txt`; runner, original auditor and its output are retained beside it for provenance. SHA-256 pins matched. The CPU auditor regenerated A/B inputs and labels from frozen seeds, verified support orders, identical arm-start hashes, routes/state controls, all 160 row-level B learning-curve records (5 seeds × 2 arms × 16 arrivals × 4,096 held-out rows), and A final predictions. The exact #3851 predecessor auditor error set contained only the 10 explained post-rollback `curve_final_mismatch` errors; no other integrity errors remained.

**Scoped result:** arrival-16 legacy mean accuracy 0.94189453125; shared-stream mean 0.941015625; paired mean shared−legacy delta −0.00087890625 (per-seed deltas are in `audit_result.json`). Thus the previously reported legacy collapse is **not reproduced by the pre-rollback trained-adapter curves**, and the `seed+31` stream shows no material rescue over `seed+35` in these five synthetic seeds. This does not repair #3851's invalid post-rollback final metrics or convert its formal allocation to PASS. See `OUTCOME.json` for exact hashes and invocation accounting.

Scope: five synthetic seeds and this paired sampling-stream comparison only. No runtime/product or broad generalization claim.
