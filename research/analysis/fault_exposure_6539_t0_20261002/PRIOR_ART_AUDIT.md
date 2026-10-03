# Issue #6539 prior-art comparator audit

Status: preparation evidence only. No local candidate was trained and no T0
experiment was run. This file does not claim novelty, efficacy, or safety.

## Frozen source identity

- Repository: [`super-jw/DA-GRPO`](https://github.com/super-jw/DA-GRPO)
- `main` commit resolved by `git ls-remote` on 2026-10-02:
  `13d3734ba249eaa7dcf1b0bea8483172de9c2b25`
- `README.md` Git blob: `c445a4af9ebb6b5c92ca739895d7e371935952e6`
- `verl/trainer/gui_agent.py` Git blob:
  `947749d2873ab8f3514ea8e74bdf0fca0c836ee1`
- `verl/trainer/perturb_utils.py` Git blob:
  `7f6cd8a3eb8f529011d50bb9842374c09b9150a8`
- `config/default.yaml` Git blob:
  `53e8dd521e1968dbf1403d94142dc3a9c491ea7f`
- Primary paper: Sun et al., [AgentHijack, ICML 2026](https://proceedings.mlr.press/v306/sun26ba.html),
  [full text](https://arxiv.org/html/2605.25707v1).

The code was inspected through the stated immutable commit, not executed.
Only the files named above and the paper sections cited by Issue #6539 were
checked; this is not an exhaustive repository or literature audit.

## Comparator matrix

| Dimension | DA-GRPO / AgentHijack evidence at the inspected scope | #6539 T0 implication |
|---|---|---|
| Policy scope | Full vision-language GUI agent (UI-TARS-1.5-7B); worker parses generated actions, creates PyAutoGUI code, and calls the desktop environment step. | Direct overlap for general corruption-trained GUI action policies. Do not claim that exposure to GUI corruption is novel. |
| Corruption | `EnvWorker` samples among pop-ups, resolution changes, marks, subtitles, and multi-app clutter; perturbations are applied at reset and after steps. README lists additional configurable corruption types. | Include a held-out non-adversarial corruption family in the local fixture, but keep its authority/effect labels source-bound. |
| Authority-absence label | **UNKNOWN.** The inspected worker maps `call_user` and `error_env` tokens to `FAIL`; this does not establish how authority absence is represented elsewhere in the stack. | Do not assert external absence of authority-aware labels. Independently label missing authority/effect evidence as YIELD in our own fixture. |
| Action-admission mechanism | In the inspected worker step, parsed model output is converted to PyAutoGUI code and passed to `env.step`; no separate deterministic proposal/admission boundary is visible in that function. Whole-stack admission behavior is **UNKNOWN**. | A deterministic admission boundary is a required local invariant, not an inferred external novelty. |
| Abstention / YIELD | No explicit YIELD outcome is visible in the inspected action path; `call_user` becomes `FAIL`. Whole-stack abstention behavior is **UNKNOWN**. | Keep a distinct YIELD label and score correct versus unnecessary YIELD. Do not treat blanket abstention as recovery. |
| Effect oracle | Paper reports task-success and action-format reward. The inspected worker exposes environment reward/evaluation; whether that is an independent effect oracle for forbidden/wrong-target actions is **UNKNOWN**. | Audit with an independent fixture ledger; do not import task-success as a safety endpoint. |
| Denominator | Exact all-attempt denominator and treatment of reset/trajectory failures are **UNKNOWN** in this bounded code review. | Preregister intention-to-test denominators over every eligible episode, including abstentions and failures. |
| Scale / equal-budget feasibility | The paper/release describes 7B multimodal training, 128 AgentHijack tasks, multi-environment rollouts, Ray, and Docker/OSWorld infrastructure. | A matched full-method run is not feasible at the proposed local T0 budget. Make no superiority claim to DA-GRPO; compare only frozen local arms and state this gap. |

The local #2526 translation/noise augmentation study is not an executable exact
baseline here: its preserved stop is `STOP_SOURCE_MANIFEST_UNAVAILABLE` because
the source-bound X11 train/shift manifests and frames are unavailable. The
#6539 synthetic visual-channel arm must not be described as a replication or
matched #2526 arm; preserve #2526 and its parent #2394 outcomes unchanged.

## Decision impact

This audit narrows the residual question; it does not resolve external novelty.
The falsifiable local question remains whether equal-budget fault exposure in a
bounded proposal-only policy changes held-out authorized-effect completion and
unsafe accepted proposals versus clean-only training and a deterministic rule,
with authority/effect loss requiring YIELD and admission held fixed. A useful
recovery pass must improve absolute authorized-effect completion on the full
eligible denominator by a prospectively frozen practical margin. Correct-YIELD
gain alone is triage-only; blanket YIELD beyond the frozen completion
non-inferiority margin is `HOLD_NO_USEFUL_RECOVERY`.

Before any candidate run, freeze the episode generator, task/fault-family split,
training rows and compute per arm, seed schedule, practical and
non-inferiority margins, confidence procedure, all-attempt denominator,
container image identity, outputs, and raw-only independent auditor. The
experiment remains gated on current-main refreeze and non-conflicting WSLc
authorization. Preserve this audit if later evidence changes the comparator.
