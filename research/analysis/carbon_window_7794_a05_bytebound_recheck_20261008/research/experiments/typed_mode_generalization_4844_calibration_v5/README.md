# Typed-mode calibrated selective-risk successor

This directory contains fresh allocation `typed-mode-4844-risk-calibration-20260928-01` for Issue #5198. It asks whether the typed-mode classifier's selective-risk result changes when each arm's single confidence threshold is calibrated to a shared 65% pooled coverage on independent data, before evaluation on a separate heldout set.

The predecessor allocation -04 remains a separate fixed-threshold result (`HOLD_COVERAGE_TRADEOFF`) and is neither edited nor pooled. Read [PLAN.md](PLAN.md) before interpreting any result. All evidence is synthetic and finite-family only; no runtime, GUI, model-quality or product claim follows.

The formal output is preserved under `formal/allocation-01/` with a runner receipt and independent raw-only audit once executed.
