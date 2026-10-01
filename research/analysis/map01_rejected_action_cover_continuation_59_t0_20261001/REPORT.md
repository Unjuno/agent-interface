# Result — #59 rejected-action / continuation boundary T0

**Disposition: `PASS_METHOD_SCOPED` (retrospective host construction only).**

On the retained v39 decision-1 values, the primary action floor is
`max(35, 97 - 8) = 89`; current health 85 rejects that action. The separately
authored continuation floor is `max(25, 97 - 12) = 85`; equality admits only
the bounded continuation in this arithmetic model. The independent six-row
oracle passed. Health 84, absent health, stale evidence (30,001 > 30,000 ms),
and mismatched source all reject continuation. Health 86 passes continuation
while still rejecting the primary action. Every row records
`input_authority: false`.

The result makes one narrow fact precise: action refusal does not logically
imply that a separately bounded continuation contract must also fail. It does
**not** show that the continuation remains appropriate when the primary action
was refused, that executing it is safe, or that doing so improves the live
control gap. In particular, the retained trace supplies health validity but
this experiment does not establish fresh enemy-relative policy suitability.
The production v39 controller remains unchanged; no runtime integration is
recommended from this result alone.

## Verification

- TDD RED: initial test import failed because `candidate.py` did not yet exist.
- TDD GREEN: 6/6 finite candidate tests passed.
- Candidate: two host executions total (the second used the finalized output
  path); six output rows retained from the second invocation.
- Independent auditor: one host execution; `PASS_METHOD_SCOPED`, 6 cases,
  zero mismatches.
- Python compilation passed for candidate and auditor.
- No Docker/container or formal allocation was used; no model/GUI/game/input.
- The inherited T4 worktree and its empty inspect receipt were not modified.

See [PLAN.md](PLAN.md), [candidate.py](candidate.py),
[candidate output](candidate_output.json), [auditor.py](auditor.py), and
[audit](audit.json). The six-case result is construction evidence only; its
protocol was documented after the first candidate invocation and is explicitly
not preregistered.
