# Successor #3780: cross-process role skill reload

Issue #3890; predecessor #3780. Branch `research/needle-role-skill-reload-3780-20260921`; additive path `research/needle_role_skill_reload_3780_v1/`.

## H/T/D/C/U

**H:** The receipt-gated A→B→C learned role adapters from #3780 can be exported as inert, schema-bounded JSON numeric tensors and reloaded in two clean CPU containers with bit-identical held-out predictions and generation-bound graph behavior.

**T:** One training-builder container and two separate fresh loader containers per seed; fixed seeds 3781, 3782, 3783. Reuse #3780 8/16/4 architecture, rank-2 adapters, 512 base / 16 support rows, 400 / 120 AdamW steps, 4096 heldout rows per role, single CPU thread and deterministic PyTorch. Artifact permits only fixed schema, architecture, roles, tensor names, numeric shapes/values, and a SHA-256 digest; no code execution, pickle, network, or dynamic imports from the artifact. Compare every 4096 prediction per role from both loaders to builder output. Exercise A→B→C twice with fresh fixture receipts; reject replayed prior-generation receipt, tampered digest, truncation, unknown schema, wrong adapter version, skipped edge, wrong scope, duplicate receipt, unverified result, and unknown destination without state mutation or fixture emission.

**D:** PASS only if all three seeds achieve >=.90 accuracy for all roles, base weights remain unchanged, both fresh loader processes reproduce all 12,288 predictions exactly per seed, all graph flows and negative controls meet specification, and independent audit reports zero errors. Any missing/invalid output is STOP; no retry or seed substitution.

**C:** Docker `needle-pilot05:local`, `--network none`, CPU 1, memory 2g, repository input read-only, distinct output directory per role. No host model training; no GPU, downloads, runtime authority or application effects. Preformal construction checks are not formal results. The formal allocation is one orchestration containing the three predeclared seeds; preserve all raw outputs.

**U:** Synthetic family, 3 fixed seeds, hand-authored graph and fixture oracle. SHA-256 is integrity, not authenticity. No real skill transfer, production authorization, adversarial security guarantee, concurrency, or product-level claim.

## Formal outputs

Retain the exact freeze manifest and source hashes, builder metadata, artifact, builder predictions, both loader outputs, independent audit, and checksums under this directory. Formal artifacts are immutable after invocation; any auditor correction is separately versioned and disclosed.
