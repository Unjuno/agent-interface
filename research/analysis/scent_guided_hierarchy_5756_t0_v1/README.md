# Issue #5756 — finite menu-search T0

## H / T / D / C / U

- **H:** On unfamiliar, ambiguous GUI hierarchies, a source-bound cue/backtrack policy can find an independently specified target at lower end-to-end search cost than equally safe exhaustive and strongest-cue policies, with no forbidden effect. T0 cannot establish this live hypothesis.
- **T:** Run the frozen five-policy matrix over five finite fixtures, with identical task, start state, observation visibility, reversibility gate and 12-call budget. Policies: scent+backtrack, exhaustive DFS, strongest visible saliency with recovery, direct app search when exposed, and a FIFO step-level tree-search baseline. The set includes misleading cues/epoch invalidation, no target, no safe path, budget exhaustion, and an exposed direct-search shortcut.
- **D:** `PASS_METHOD_SCOPED` requires the independent audit to replay every environment event, verify target claims/cost/budget/epoch/safety, confirm paired visibility, and reject all four preregistered mutations. A target is known only after its current screen has been observed. No result here is evidence of lower live cost or an LLM benefit.
- **C:** A direct search/command palette or stronger whole-screen reasoning can beat hierarchical exploration. The tree baseline here is a small deterministic FIFO policy, not a reproduction of Agent Alpha/MCTS.
- **U:** Hand-authored finite graphs do not represent GUI dynamics, OCR noise, language variation, model behavior, or environmental timing; five fixtures cannot support a statistical/general superiority claim.

## Frozen protocol

`spec.json` is the complete paired fixture and budget definition. Candidate policies receive only a callable observation/navigation API; the harness retains graph transitions and target oracle. The independent `audit.py` imports neither candidate nor runner. It cross-checks candidate traces against a separately retained environment event stream and independently replays both against the fixture oracle. `test_t0.py` includes the four controls: hidden-label leak, omitted navigation, altered epoch, and wrong-target success claim.

Frozen scent score: exact task-token matches in the union of the currently visible edge label and nearby text, plus `saliency / 100`; ties break by edge ID descending. Strongest-cue uses saliency only. Exhaustive is stable display-order depth-first with backtracking; tree search uses a FIFO frontier populated only from observed safe edges. These are deterministic reference baselines, not optimized or learned agents.

Primary endpoint is target observed within budget and zero forbidden effects. Search costs are compared only among equally correct/safe eligible arms; cost components remain separately reported. No-target and no-safe-path are explicit eligibility/refusal cases. Direct-search arms are ineligible only on fixtures that do not expose that affordance. All matrix rows remain in the intention-to-test count.

## Execution boundary

Finite CPU-only/no-model method test; no GPU, GUI, network, container or external side effect. This allocation is not a live T1 and makes no claim about Agent Interface product behavior. The local execution was on the Windows host because the already-reviewed container lane is shared/unavailable for this task; do not infer container isolation from the source API boundary.

