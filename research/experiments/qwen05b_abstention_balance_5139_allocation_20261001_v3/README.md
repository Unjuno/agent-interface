# Qwen support-balance #5139 — CPU construction only

This package records the `QWEN-SUPPORT-BALANCE-5139-20261001-03-CPU-CONSTRUCTION` synthetic dataset build and independent integrity audit. It is evidence for data construction only, not the planned local RTX 3080 LoRA comparison.

- [Frozen plan](PLAN.md) and [source/resource freeze](FREEZE.json)
- [Formal dataset bytes](formal-dataset.json), [candidate receipt](CANDIDATE.json), and [independent audit](AUDIT.json)
- [Run ledger](RUN.json), [scoped result](REPORT.md), and [SHA-256 manifest](SHA256SUMS.txt)

The candidate was run once; a separate raw-only auditor reconstructed it and rejected all five corruption controls. Tests are synthetic CPU checks. No Docker/OrbStack/WSL, model/tokenizer, GPU/CUDA, fit, or adapter operation occurred. Historical `sad_cannon` attribution remains UNKNOWN. See the report for the remaining #5139 formal start gates and scope limits.
