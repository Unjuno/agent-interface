# Issue #5322 — strategic reporting research

This additive package contains two separate studies. The primary study is a one-shot, theorem-free no-model simulator with paired task inputs, frozen seeds, raw per-arm traces, and an independent auditor. A second descriptive pilot probes prompt-conditioned reports from two local quantized models on the RTX 3080 Laptop GPU. Its outputs must not be pooled with the simulator or used to claim real strategic behavior.

## Scope and authority

Scores and reputations are advisory research signals only. Neither study tests authority, safety gating, or integration. The synthetic utility scale, one-shot best-response assumption, perfect source-audit oracle, finite strategy set, and posterior-only model prompts limit interpretation. The local-model pilot tests prompted behavior, not autonomous incentives or calibration in deployment.

## Source freeze and commands

See FREEZE.json for input SHA-256 values, main base, model digests, exact commands, and allocation boundaries. The CPU simulator command is `python -B simulator.py --output results/formal-01`, followed once by `python -B audit.py results/formal-01/raw.jsonl results/formal-01/summary.json --output results/formal-01/AUDIT.json`. The separately preregistered local GPU command is `python -B gpu_model_pilot.py --output results/gpu-pilot-01`, followed by `python -B audit_gpu_model_pilot.py results/gpu-pilot-01`.

Construction tests use only seed 901337 and two-task cells. The formal simulator uses only the seeds and 80-task cells named in PREREGISTRATION.md. Do not rerun, replace, or pool formal outputs. Retain STOP on source, audit, GPU placement, or resource failures.
