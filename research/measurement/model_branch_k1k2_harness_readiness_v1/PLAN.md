# MODEL-BRANCH-K1K2-HARNESS-READINESS-20260918-001
H: A K1/K2 model-cost pair can isolate branch allowance with one single-generation call per arm, but this container may lack the approved Codex CLI runtime.
T: Freeze one prompt template differing by exactly one ASCII digit; strict no-authority output parser; JSONL usage/arrival extractor; explicit one-generation-per-arm plan; runtime preflight checks existing Node/Codex paths only and never launches/installs model software.
D: PASS only if static harness gates pass and approved Codex CLI path is executable/readable. HOLD_MODEL_RUNTIME_UNAVAILABLE if static gates pass but CLI absent. FAIL on prompt mismatch, second-generation K2, parser authority leak, source mismatch.
C: Executable requested CLI still would not prove served model identity or complete hidden-context isolation.
U: Harness/readiness only; no model/token/quality result.
