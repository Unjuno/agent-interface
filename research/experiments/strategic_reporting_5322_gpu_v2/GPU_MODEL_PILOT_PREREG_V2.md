# Successor preregistration for Issue #5397

This new allocation corrects only the locally observed Qwen3 model digest after GPU pilot-01 stopped before inference. Pilot-01 remains immutable; this is a separately frozen successor and may be invoked once only.

---

# GPU local-model reporting pilot — preregistration

This is a small exploratory complement to the no-model simulator, motivated by Issue #5322's explicit uncertainty about whether synthetic incentives resemble learned verifier behavior. It does not replace or pool with the preregistered simulator result.

## H/T

With identical posterior-only evidence, two already-installed local instruction models may produce more confident reports when routing rewards confidence than when reports receive proper Brier scoring; proper scoring should keep reports near the supplied posterior. UNKNOWN is a permitted response. The pilot tests prompt-conditioned behavior, not autonomous economic strategy.

Use `qwen2.5:3b` and `qwen3:4b` from the already-running local Ollama service. Both are present before this preregistration; no model download or external request is permitted. The exact Ollama model digests are recorded in `FREEZE.json`. Run three fixed prompt conditions once each per model: metadata/routing reward, delayed outcome Brier scoring, and outcome Brier scoring plus 20% random audit. Keep model temperature 0 and generation seed 20260930. Each prompt contains the same 16 posterior cases (`q` values 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.45, 0.40, 0.35, 0.30, 0.25, 0.20, 0.15, 0.10), in the same order. Outcomes are generated once from `Bernoulli(q)` with seed 748219963 and are withheld from the model.

For each mechanism, request one probability report or UNKNOWN per case. Record exact prompt, raw response, parsed response, HTTP timing, model digest, generation options, `ollama ps`, `nvidia-smi`, and source hashes. No retries, replacement outputs, prompt repair, model substitution, pooling, or post-result tuning. Invalid schema is retained as a pilot failure.

## D/C/U

Report per-model mean absolute deviation from supplied q, Brier score against withheld outcomes, overclaim rate (`abs(p - 0.5) >= abs(q - 0.5) + 0.20`), UNKNOWN rate, parse failures, and the mechanism-paired differences. Descriptive only; no significance test, PASS threshold, prevalence estimate, model ranking, or mechanism guarantee is claimed from 16 cases per cell.

The GPU run is accepted only if Ollama reports the model on GPU and the recorded CUDA device is the local RTX 3080 Laptop GPU. If inference falls back to CPU or a call fails, retain STOP and do not retry. This is local prompt-response behavior from two quantized models under one fixed prompt and one generation seed. It does not show real learned-model incentives, strategic adaptation, calibration in deployment, authority safety, or generalization.
