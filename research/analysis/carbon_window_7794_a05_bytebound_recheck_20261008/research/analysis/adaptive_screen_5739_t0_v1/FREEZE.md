# Issue #5739 T0 pre-execution freeze

## H / T / D / C / U

- **H:** In the frozen finite test world, a claim-aware screening protocol refuses unadjusted promotion among multiple survivors, never claims global optimality when a screened-out arm is best on sealed outcomes, and stops promotion for a safety-failing survivor despite its favorable success count. A separate raw-only auditor must reconstruct all attempts and reject every declared corruption.
- **T:** One deterministic finite host-only candidate run and, only after exit 0, one independent raw-only audit. Scenarios: two survivors sharing one sealed cohort and baseline; a screened-out arm with the best sealed outcome; and a fastest arm with a forbidden effect. Controls: missing attempt, duplicate attempt, repeated sealed variant, changed comparison family, forged safety record, unsupported global-best claim, and unadjusted promotion. Candidate/auditor source and world are committed and read back before execution.
- **D:** `PASS_CLAIM_BOUNDARY_SCOPED` only if all three scenario labels match the frozen rules, no global-optimality claim appears, all 32 assignments reconcile independently, and all seven corruption controls reject. Any unsupported/global/safety-invalid claim is `FAIL_CLAIM_BOUNDARY`; otherwise unresolved correctness is `HOLD_INSUFFICIENT_CONFIRMATION`.
- **C:** A single predeclared survivor-vs-baseline comparison with a fixed non-statistical gate may not need multiplicity adjustment. This authored finite world has no calibrated probability model and may not be read as a significance test.
- **U:** Deterministic authored fixtures only. No empirical performance, GUI/model/task effect, shared-resource savings, Docker/container, safety, or product claim.

## Immutable execution contract

- Repository: `Unjuno/agent-interface`; exact base main: `24f6b7d5f9395105807f981d48db212e6692a6f4`.
- Branch: `research/5722-claim-boundary-successor-20261001`.
- Result path: `research/analysis/adaptive_screen_5739_t0_v1/`.
- Host: Windows x86_64, CPython 3.12.10. Execution is CPU-only, deterministic, network-free, and has no external effects.
- Candidate command: `python -B runner.py`, at most once. Output must not already exist.
- Auditor command: `python -B audit.py`, at most once and only if the candidate exits 0. It consumes only the saved raw and frozen world; it does not import candidate code.
- Docker is not invoked: no #5085 CPU/container slot is assigned to this issue, the Docker engine service is stopped, and existing container ownership is unresolved. No Docker inventory or lifecycle command is authorized by this freeze.
- No model, GPU, GUI, game, X11, input, network, retries, reseeding, or post-outcome threshold changes.

## Frozen SHA-256

- `world.json`: `5329331f1948d7db6fb58244473dddbc1391c841c709b6de9b8ede31a7316441`
- `runner.py`: `f9e0d06048538c8e942ed450938b8550348aafc0a093be2c6f17c8fc9b7448bc`
- `audit.py`: `469c0555d875f998a85f545419fb3a92f344287f1515a014880ab50e9290e3b5`

Output files `candidate_raw.json` and `audit_result.json` were absent at freeze time. The prior #5722 T0 / PR #5733 is retained unchanged and is not pooled with this successor.
