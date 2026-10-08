# Issue #5306 T0 — adaptive-submodularity boundary

This additive successor tests one unverified #5306 comment: a pair of checks may have zero single-step decision value but positive joint value. Start with [PLAN.md](PLAN.md), then inspect the frozen model and independent audit implementation.

Candidate input is `model.json`; `candidate.py` implements only myopic net-VOI, while `audit.py` independently enumerates exact continuations. Formal result and exact command receipts are retained under `results/` after freeze. The experiment is a constructed rational model, not a calibration or runtime study.

Host-only Python standard-library run. No model, GUI, network, game, task effect, user data, Docker container, or shared container interaction.
