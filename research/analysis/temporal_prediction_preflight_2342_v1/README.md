# Temporal prediction sampling preflight (#2342)

## H/T/D

The hypothesis in #2342 concerns model-facing GUI decision utility, not merely local predictor error. The Docker preflight enumerated the required gates before allocation: two live application-like workflows, one model/policy allocation, independent future-state/effect scoring, raw-history control, reversal/occlusion/disappearance cases, model/token/latency accounting, and a held-out second surface.

All seven gates are missing in this preflight. The run used `python:3.12-slim` resolved to `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; result SHA-256 is `c9e43f62b50027abc89a49487ccc1dadc1e473f421496ea865d14a9c111f409d`.

## C

A synthetic predictor or authored trajectory could improve pixel error while the model ignores it or acts unsafely on reversal, stale, disappeared, or occluded targets.

## U / stop

Disposition: `STOP_LIVE_MODEL_GUI_NOT_EXECUTED`. No model, GUI, input, network, or prediction run was performed. This is a readiness stop, not a PASS/FAIL of age-based sampling.
