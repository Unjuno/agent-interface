# Observation load and feedback cascades

These Issues study adjacent mechanisms, but their outcomes are separate. Neither authorizes changing mandatory observation, freshness, release, or effect-verification behavior.

## Observation load versus cue information — #8665

**Idea.** Separate the computational/scheduling load of observation from information carried by its cue, and test whether a reactive response changes their effects.

**Evidence.** The preregistered 2×2×2 finite CPU fixture ran 256 attempts across four regimes and eight matched seeds. An independently implemented raw-only auditor returned `PASS_METHOD_SCOPED`, zero errors, and rejected 5/5 frozen mutations. The observed contrast was classified `MIXED_SCOPED_FIXTURE`, not a general load or information effect. It used no live GUI, OS input, model, container, or external service. The result is retained through [PR #8700](https://github.com/Unjuno/agent-interface/pull/8700); [Issue #8665](https://github.com/Unjuno/agent-interface/issues/8665) remains the source for its exact scope.

## Recurring observation demand under load — #8888

**Idea.** Test whether observation demand that responds to queue delay can create a self-amplifying feedback loop under bounded service capacity.

**A01 disposition.** Allocation `8888-observation-feedback-cascade-a01-20261012-01` ran once on Windows CPython 3.12.10. The candidate emitted `NO_AMPLIFICATION_SCOPED`, but post-run review found the sustained-arrival event ordering did not implement the frozen FIFO equation, two controls were hard-coded, and the auditor neither independently reconstructed the scheduler nor executed its claimed mutations. The accepted disposition is `STOP_IMPLEMENTATION_AUDIT_FAILURE`; this is not a scientific null result. Candidate and auditor were not rerun. The allocation is consumed and its retained evidence remains at `research/analysis/observation_feedback_cascade_8888_a01/`; see the full [Issue #8888 outcome](https://github.com/Unjuno/agent-interface/issues/8888).

This STOP applies to the integrity of that allocation's result. It does not stop other workers or authorize changing observation policy. Any successor needs a new frozen allocation with a real discrete-event scheduler, exercised controls, and an independent auditor that reconstructs the trace and actually applies mutations. The issue reports no live GUI defect, operational threshold, or runtime benefit.

## Relationship

#8665 isolates load and cue content in a one-shot finite factorial. #8888 proposes endogenous repeated demand and queue dynamics. A method pass in the first does not validate the second; the second's STOP does not invalidate the first. Neither supports production or user-facing claims.
