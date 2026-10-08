# Construction failure A01 — independent verifier root path

The first verification attempt (`verify.py`) exited 1 before the independent recount. It computed the repository root one directory too high and raised `FileNotFoundError` for `/mnt/d/codex-research/research/live_control/results/integrated-efficiency-live-01-summary.json`.

This was an auditor-construction defect, not a scientific or allocation outcome. The candidate `audit.py` had already completed with exit 0. The first failure remains preserved; `verify.py` was corrected to resolve its repository root from the package directory's actual parent depth. The corrected verifier is a separate attempt and does not change any historical study data.
