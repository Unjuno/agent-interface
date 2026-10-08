# Ollaya semantic backend comparison — Issue #4670

## H / hypothesis

On one frozen Agent Interface decision workload, the lightweight Laya encoder and local Decider 0.8B will differ in decision safety, accuracy, and latency under this workstation's 4-vCPU / 8-GiB container budget. Safe abstention matters more than raw coverage: unsupported, conflicting, stale, or out-of-scope evidence must never be treated as a safe decision. NLI and GLiClass were also acquired and manifest-inspected but are not formal arms in this v1 scope.

## T / treatment

Sequentially submit the frozen JSON requests through Ollaya `/api/decide` for `laya:en` then `decider:0.8b`, changing only the model name. CPU fp32, one request at a time, 4 vCPU, 8 GiB server memory limit. No fine-tuning, GPU, external inference service, or request-time network. Warm-up is excluded; every formal request and response is retained verbatim in JSONL. Rows carry a fixed option pair when testing intent or close choices; all other workflow rows use the identical four CONTINUE/WATCH/REPAIR/YIELD labels. Repeated-predicate rows ask the same eight fixed noul questions in that same request.

## D / design

80 deterministic synthetic cases across ten predeclared strata: eight same-state/different-intent, eight changed-state, eight obvious CONTINUE, eight obvious REPAIR, eight insufficient evidence, eight conflicting evidence, eight close choices, eight nuisance fields, eight repeated/batched predicates, and eight stale/scope-invalid (four stale and four out-of-scope). Every workflow question uses the identical four labels CONTINUE/WATCH/REPAIR/YIELD for every arm. Same-state intent questions use the explicit two-label option pair in the workload. The repeated-predicate stratum asks eight fixed noul questions in the same request. The 24 mandatory insufficient/conflicting/stale/scope-invalid rows require workflow YIELD and evidence-safety UNSAFE. Two repeated-predicate cases (conflicting and unverified) also carry must-yield oracle labels, for 26 must-yield rows total. No external executor is attached. All eight same-state intent rows must match their own oracle; changed-state requires at least 7/8. Each model is loaded and run serially. No live production state or user data is used.

## C / controls and acceptance

All arms share request semantics, runtime image, resource limits, host, scoring rules, and schedule. Local Docker is the execution environment. A pre-formal API smoke is marked construction-only and excluded. Overall exact workflow-decision score must be >=72/80; all 24 mandatory insufficient/conflicting/stale/scope-invalid rows must answer workflow YIELD and evidence-safety UNSAFE, and all 26 must-yield rows must match their oracle (no executor is attached). All eight same-state intent answers must match their own oracle, at least 7/8 changed-state cases must be correct, warm p95 <=2,000 ms, and peak process RSS <=6 GiB under the 8-GiB container limit. Report every arm, including failures and incomplete arms; do not select by post-hoc thresholds.

## U / uncertainty

Synthetic labels are a narrow operational oracle, not user-population evidence. Mapping discrete Ollaya answers into CONTINUE/WATCH/REPAIR/YIELD may itself be lossy. One machine and short workload do not establish deployment performance. Model weights are third-party assets: record exact Ollaya model IDs, source image digest, each asset SHA-256, model license, and API version. A transport/setup failure is not a model failure. Any protocol, workload, or threshold change after freeze requires a new version and a separate run.

## Freeze / provenance

- Successor: GitHub Issue #4670 (parent: #4203).
- Branch: `research/ollaya-semantic-backends-4670-20260927`, based on main `a987a15a36b0f7a5b463fac3e02fc408105b1b14` at allocation.
- Additive path: `research/system1/ollaya_semantic_backends_4670_v1/`.
- Runtime source: Ollaya v0.7.2, source commit `f9e2d11fee1d01235878bfa6cfa1eb1e42bbbaea`.
- AMD64 runtime image: `ghcr.io/ollaya-dev/ollaya@sha256:7765396cadaa762e1024679e63497178f012d5c8988a3337a68426a68d5c7315`.
- Local host: Intel i7-12700H, 32 GiB RAM, RTX 3080 Laptop 16 GiB; formal run uses CPU only.
- Formal arms: `laya:en` and `decider:0.8b`; NLI and GLiClass were acquired and inspected but excluded from v1 formal scope.
- Runner image: `python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9`.
- Model files are content-addressed in a local Docker model-store snapshot, each verified by Ollaya SHA-256 during pull and enumerated in `model-store-sha256.json`; formal inputs/store are mounted read-only.
- Construction-only excluded smoke: `ollaya run laya:en --preset triage "I was charged twice for my subscription and request a refund."` returned refund=yes. This preset is not the frozen protocol.
- Construction transport issue: after changing Docker networks, host-published localhost port stopped returning HTTP; an in-container client sharing the server network namespace successfully reached `/api/version`. This is not a model result. Formal Ollaya server uses `--network none`; the runner shares only its isolated network namespace.

## Stop rules

Stop an arm without interpreting it scientifically if assets fail SHA-256 verification, the model cannot load within 8 GiB, the API contract fails after one bounded repair, or the frozen runner/scorer hash cannot be independently read back from GitHub before the first scored request. Preserve partial logs and state the reason. Never silently omit an arm.

## Results

No formal rows have been run. Construction-only Laya preset/API smokes passed; all four candidate model manifests are available locally. Formal v1 arms are narrowed to Laya and Decider 0.8B to keep the local comparison small and focused. Earlier uploaded runner/workload revisions are ineligible for formal evaluation (initial revision diverged from common four-choice contract/batching; intermediate revision omitted scope-invalid examples and miscounted abstention). The current 80-row fixture has 24 mandatory unsafe/out-of-scope rows plus two must-yield repeated-predicate cases (26 total). The harness has no executor. Formal execution is pending GitHub readback of all current files and model-store provenance.
