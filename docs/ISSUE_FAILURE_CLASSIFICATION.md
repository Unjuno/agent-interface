# Failure classification and Issue routing

User direction: 2026-09-22. Companion to [research method](RESEARCH_METHOD.md),
[current goal](CURRENT_GOAL.md) and the
[existing convergence gate, Issue #2789](https://github.com/Unjuno/agent-interface/issues/2789).

**One Issue should own one scientific question or integration decision.
A new allocation ID is not automatically a new successor Issue.**

## Classify before assigning work

| Evidence actually available | Record and next action | Do not infer |
|---|---|---|
| One worker lacks an engine, package, model route, permission or usable tool envelope | Keep a local environment/setup record under the original Issue; use a suitable authorized environment for any justified next allocation | Fleet-wide unavailability, product failure or a scientific result |
| Runner/auditor/collector error, missing exit receipt or incomplete measurement | Keep a harness/evidence limitation under the same question; fix construction separately or add an explicitly versioned read-only audit | Missing status, retroactive PASS, or an obligation to rerun science until a wrapper passes |
| Source/raw upload or byte readback fails | Keep publication status in the existing evidence PR/Issue; retain and verify the original bytes | A new experiment, a storage-service defect without evidence, or permission to evade a blocked operation |
| Reproducible violation of a pinned application/runtime contract | Keep the substantive defect or hypothesis; identify the affected path, minimal reproduction and controls | That an actual safety/correctness defect is unimportant merely because it was found locally |
| Failure exposed in the selected integrated entry path | Record the affected acceptance gate and evidence | A component result automatically determining every other route or the entire roadmap |

The classification is about what the evidence supports, not whether the outcome
is favourable. A failed quality gate in a complete valid experiment remains a
scientific failure. A successful raw reconstruction does not invent an
unobserved process exit. Neither type of evidence should be discarded.

## Allocation, construction and successor boundaries

Keep timeout changes, batching, launcher fixes, environment substitutions and
publication repairs in the original question's run log. Preserve each attempt's
identity, source/environment, command, output and first disposition. A local
availability statement needs the observed environment and time; it is not a
permanent repository capability statement.

Construction may be debugged and repeated with separate retained records.
Changing a consumed formal run requires a separately identified, prospectively
frozen allocation and explicit deltas, never overwriting or pooling old rows by
convenience. This rule does not require another Issue. Fresh identifiers are
traceability, not permission for unlimited repeated experiments.

A successor Issue is warranted when a genuinely different hypothesis, contract,
application boundary or required integration decision remains. State the
originating question, the changed scientific factor, why existing evidence does
not answer it, and the concrete decision its result could change. Check open and
closed Issues, PRs and ownership first. Preserve H/T/D/C/U and scoped outcomes.
Do not substitute documenting a local setup failure for testing the selected
idea, and do not start a new supervisor/auditor research chain merely to make an
old wrapper green.

A shared engineering defect can merit a bounded engineering Issue when a pinned
reproduction establishes impact on an actual shared path. Label that purpose
explicitly. It must not be promoted to a new scientific result by nomenclature.

## Parallel coordination and evidence preservation

Do not interrupt an already running or frozen finite allocation to tidy Issues.
Its existing owner should finish at the original safe stopping boundary and
retain the first outcome. An Issue kept open only for that execution or evidence
handoff must say so; it is not an invitation for another worker or a replacement
allocation. Coordinate any genuine change with the current owner.

Correct misleading titles and prepend a dated routing note; preserve original
plans, comments and result artifacts. Close redundant independent work orders
with an administrative reason, not a false scientific-completion claim. Do not
delete a branch merely because its Issue is closed: verify merged evidence,
remaining work and dependent PRs first. Publication-only problems do not justify
rerunning the scientific allocation.

## Consequences for promotion

The existing correctness, release, provenance and integration gates are
unchanged. Keep scientific disposition, evidence completeness, publication state
and product acceptance separate. A component PASS is not integrated acceptance;
an administrative closure is not PASS; a local STOP is not a fleet-wide STOP.

Use the smallest necessary engineering repair, then return to the actual
interface question. Closed-Issue counts, retained-failure counts and document
counts are not evidence of user-visible progress. This document adds no runtime
mechanism, experiment allocation, workflow or new global acceptance gate.
