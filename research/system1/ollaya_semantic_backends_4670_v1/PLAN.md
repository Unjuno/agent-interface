# Ollaya semantic backend comparison — Issue #4670

## H / hypothesis

On one frozen Agent Interface decision workload, at least one small CPU-local Ollaya backend (Laya English, Decider 0.8B, NLI DeBERTa-v3-large, or GLiClass) will reach the pre-registered decision-safety and accuracy gates within this workstation's 4-vCPU / 8-GiB container budget. Safe abstention matters more than raw coverage: unsupported, conflicting, or stale evidence must never produce an executable action.

## T / treatment

Sequentially submit the identical frozen JSON requests through Ollaya `/api/decide`, changing only the model name. CPU fp32, one request at a time, 4 vCPU, 8 GiB server memory limit. No fine-tuning, GPU, external inference service, or request-time network. Warm-up is excluded; every formal request and response is retained verbatim in JSONL. A separate batched-predicate request is reported separately from the 80 scored rows.

## D / design

80 deterministic synthetic cases, eight each in ten predeclared strata: same-state/different-intent, changed-state, obvious CONTINUE, obvious REPAIR, insufficient evidence, conflicting evidence, stale evidence, close choices, nuisance fields, and repeated batched predicates. The 24 insufficient/conflicting/stale cases require YIELD and no executable output. Same-state/different-intent requires all eight paired distinctions; changed-state requires at least 7/8. Each model is loaded and run serially. No live production state or user data is used.

## C / controls and acceptance

All arms share request bytes, runtime image, resource limits, host, scoring rules, and schedule. Local Docker is the execution environment. A pre-formal API smoke is marked construction-only and excluded. Overall exact safe-decision score must be >=72/80, all 24 unsafe-evidence cases must YIELD with zero executable outputs, all eight intent pairs must be distinguished, at least 7/8 changed-state cases must be correct, warm p95 <=2,000 ms, and peak process RSS <=6 GiB under the 8-GiB container limit. Report every arm, including failures and incomplete arms; do not select by post-hoc thresholds.

## U / uncertainty

Synthetic labels are a narrow operational oracle, not user-population evidence. Mapping discrete Ollaya answers into CONTINUE/REPAIR/YIELD may itself be lossy. One machine and short workload do not establish deployment performance. Model weights are third-party assets: record exact Ollaya model IDs, source image digest, each asset SHA-256, model license, and API version. A transport/setup failure is not a model failure. Any protocol, workload, or threshold change after freeze requires a new version and a separate run.

## Freeze / provenance

- Successor: GitHub Issue #4670 (parent: #4203).
- Branch: `research/ollaya-semantic-backends-4670-20260927`, based on main `a987a15a36b0f7a5b463fac3e02fc408105b1b14` at allocation.
- Additive path: `research/system1/ollaya_semantic_backends_4670_v1/`.
- Runtime source: Ollaya v0.7.2, source commit `f9e2d11fee1d01235878bfa6cfa1eb1e42bbbaea`.
- AMD64 runtime image: `ghcr.io/ollaya-dev/ollaya@sha256:7765396cadaa762e1024679e63497178f012d5c8988a3337a68426a68d5c7315`.
- Local host: Intel i7-12700H, 32 GiB RAM, RTX 3080 Laptop 16 GiB; formal run uses CPU only.
- Construction-only excluded smoke: `ollaya run laya:en --preset triage "I was charged twice for my subscription and request a refund."` returned refund=yes. This preset is not the frozen protocol.
- Construction transport issue: after changing Docker networks, host-published localhost port stopped returning HTTP; an in-container client sharing the server network namespace successfully reached `/api/version`. This is not a model result. Formal server and client will share a private loopback namespace with no external network.

## Stop rules

Stop an arm without interpreting it scientifically if assets fail SHA-256 verification, the model cannot load within 8 GiB, the API contract fails after one bounded repair, or the frozen runner/scorer hash cannot be independently read back from GitHub before the first scored request. Preserve partial logs and state the reason. Never silently omit an arm.

## Results

No formal rows have been run. Construction-only Laya preset smoke passed; Decider 0.8B pull is available locally. Formal execution is pending completion and hashing of all four model assets and GitHub readback of this protocol.
