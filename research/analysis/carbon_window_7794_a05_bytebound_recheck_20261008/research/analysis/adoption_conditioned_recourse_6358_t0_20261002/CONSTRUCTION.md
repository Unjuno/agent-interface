# Construction history (not formal results)

Allocation: `ADOPTION-CONDITIONED-RECOURSE-6358-T0-HOST-20261002-01`.

- Host: Windows AMD64, CPython 3.11.9, standard library only.
- v1 (before Issue comments 5943195315 and 5943274533 were incorporated): 13 tests passed; one candidate and one independent-auditor CLI smoke were run before full freeze. Their raw files and hashes remain preserved in `results/construction-smoke-01/`. They are superseded construction records only and are never reused as v2/formal results.
- v2: updated for cohort assignment/identification limits, public warning + bounded stagger vs source-bound recipient routing, wording placebo, equal per-offer advice budget, resource authorization/latency adversarial controls, class disparity and queue/capacity audit. Construction suite: 16 tests passed; eight separate corruption checks are rejected. JSON fixtures and `git diff --check` passed. No v2 candidate/auditor CLI invocation and no formal candidate/auditor invocation occurred before freeze.
- Formal budget: candidate at most one invocation; independent auditor at most one invocation after candidate exit 0; retries zero.
- No GPU/CUDA/model, Docker/Podman/WSL, network, GUI, human participant, production service, or external effect used.
