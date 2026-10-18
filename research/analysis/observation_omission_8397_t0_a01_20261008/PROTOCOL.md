# Issue #8397 T0 A01 — finite observation-omission contract

Status: pre-freeze candidate. No formal candidate/auditor invocation has been
made at this point. This package is limited to a deterministic method fixture;
it does not evaluate GUI agents, models, runtime behavior, safety, or task
benefit.

## H / T / D / C / U

- **H (parent-issue transfer hypothesis):** For at least one frozen task/policy
  family, observation dependence varies with task state and omission duration:
  some omission cells preserve exact independently verified effects and hard
  safety outcomes while reducing model-facing observation cost, while other
  cells produce regret. This T0 does not test that empirical hypothesis.
- **T0:** Evaluate five deterministic cases: optional observations omitted
  before a sensitive decision; an omission crossing a required transition;
  captures after verified completion; captured-but-undelivered information;
  and a mandatory safety cue inside an optional-omission interval. Compare each
  intervention with its baseline. The independently authored auditor rebuilds
  interval membership, model visibility, bytes/counts, exact effect, stop
  outcome, and regret directly from the immutable fixture. No GUI, model,
  user data, runtime, OS input, network, or GPU is involved.
- **D:** `PASS_METHOD_SCOPED` only if all five frozen discriminators hold and
  the independent auditor rejects all five mutation controls (false visibility
  for undelivered capture, suppressed mandatory cue, post-completion visibility,
  forged effect, and forged cost). Otherwise `FAIL_METHOD`. This is a T0
  contract check, not H_PASS_SCOPED.
- **C:** The finite rules may be internally consistent yet fail to represent
  stochastic models, non-Markov GUI state, divergent trajectories, shifted
  recovery cost, or independently scored application effects.
- **U:** One authored finite fixture only. No empirical observation value,
  safety, task success, generalization, or production scheduler claim follows.

## Frozen semantics

Ticks are abstract deterministic task steps and are not wall-clock durations.
Intervals are half-open `[start,end)`. An event is visible to the model only if
it was captured, delivered, and strictly before the frozen completion tick.
Only optional events may be omitted. Mandatory safety events bypass the
omission interval. Model-facing call count and bytes count events that are
actually visible; a captured-but-undelivered payload contributes neither.
Exact-effect scoring is keyed to preregistered required observation identities;
in the safety case, the required effect is a stop caused by the mandatory cue.
No absent event is treated as proof of safety.

## Expected rows and mutation controls

The fixture has five scenarios, each with baseline and intervention (10 arms).
The frozen decision expects: (1) pre-decision omission retains exact effect and
reduces both visible event count and bytes; (2) transition omission exposes
effect regret; (3) post-completion capture remains invisible in both arms and
does not change cost; (4) captured-but-undelivered information is not model
visible and cannot satisfy the required cue; (5) a mandatory cue remains
visible and produces the safe-stop outcome even when the interval overlaps it.
The auditor must reject each mutation listed in D.

## Execution boundary

The WSLc shared-lane gate remains active for container commands. The formal T0
candidate and auditor are therefore planned as local standard-library Python
processes on the attached Windows workspace; no WSL, WSLc, Docker, GUI, model,
or game process is started. This execution environment distinction will be
preserved in the raw run record and limits; it is not evidence about WSL or
container performance.
