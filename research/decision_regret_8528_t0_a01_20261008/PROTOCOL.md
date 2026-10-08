# Frozen protocol — Issue #8528 T0 A01

## Scope and estimand

Finite deterministic method test of retrospective decision regret integrated only over ticks with an explicitly open decision opportunity. At each eligible tick, the comparator is the minimum toy loss over that same tick's admissible action set. Toy loss is 0 for an action equal to the exact finite target state, 1 otherwise. The integral is a sum over eligible discrete ticks, in synthetic regret units. It is not calibrated to human, product, or task value.

Evidence age is current tick minus observation tick only when the clock is comparable and the difference is nonnegative. Otherwise age is unknown. Age is reported, not used as a substitute for regret. Unknown truth/clock yields no numeric integral. An interval with no open opportunity is NOT_APPLICABLE, not zero. Causal attribution is separately marked NOT_IDENTIFIED where the fixture does not identify actual use. A hard safety event or inadmissible selected action is a separate FAIL_HARD_SAFETY with no regret scalar; safety is never traded against utility.

## H/T/D/C/U

- **H:** the two primary cases have identical candidate-visible rows and identical open-window age sequence `[3,4,5]`; they also tie on age-only sum (12) and toy unsafe-exposure duration (0), while exact audit truth gives regret integral 0 in the stable case and 3 in the changed case. Supporting controls: fresh-but-misleading evidence gives positive regret; no opportunity is not applicable; changing admissible actions constrains the comparator; missing truth/clock stays unknown; hard safety remains a separate failure; unidentified causal use receives no causal claim.
- **T:** finite, synthetic, deterministic T0 only. No GUI/model/human/runtime change, no container requirement, no user outcome, and no causal claim.
- **D:** eight finite cases; 22 total ticks. Candidate-visible and audit-only truth/loss are separate files/interfaces. Exact enumerator independently rebuilds all candidate rows and computes the finite oracle. Seven deliberately corrupted truth/opportunity/action-set/clock/safety/loss/lineage probes must be rejected.
- **C:** equal-age primary pair is the contrast; stable truth, changed truth, misleading fresh evidence, closed opportunity, time-varying action set, hard-safety event, unidentifiable use, and unknown truth/clock are controls. The selection rule remains the same simple delivered-state choice, and no observation-acquisition policy is evaluated.
- **U:** strongest bounded uncertainty is external validity: a toy binary loss cannot represent real task value, user burden, or operational safety. This T0 can validate arithmetic and boundary handling only. Any applied utility or live-agent use requires a separately specified successor experiment and authority.

## Frozen gates

Expected per-case results are encoded in `audit.py::EXPECTED`. The audit also emits age-only sums and a separately labeled toy unsafe-exposure duration. The primary pair must tie on both comparator cards (age sum 12, unsafe exposure 0) while differing on integrated regret (0 vs 3). Overall pass is `PASS_METHOD_SCOPED` only when all eight frozen dispositions, values, and age sequences match; candidate rows match the visible grid exactly; all seven truth/opportunity/action-set/clock/safety/loss/lineage mutation probes are rejected; and causal/safety boundaries are preserved. Any discrepancy is `FAIL_METHOD`. This gate is not evidence that the metric improves decisions in practice.

## Pre-formal amendment history

The initial source-only preregistration commit `353ce273ad26f61866ffcdd9f8c1eb403f57d50f` was read back before any formal invocation. That readback exposed stale wording (“five” probes) after construction had expanded the auditor to seven controls. The original commit remains immutable evidence; this additive protocol correction supersedes it before formal execution. Candidate and auditor formal counts at amendment time remain 0/1 each. The corrected freeze is the branch head containing this revision and its source/blob readback must be checked before formal execution.

## Execution and stop rules

1. Finish construction tests before pre-registration commit.
2. Commit this protocol, candidate, audit implementation, fixtures, and tests to the dedicated issue branch; source-only pre-formal corrections remain additive and must state why they supersede the prior source freeze.
3. Read back every committed blob at the corrected branch head and verify its Git blob SHA against the local bytes. This freezes the exact pre-formal source.
4. Add a GitHub issue comment with the superseded and corrected freeze commits and intended one candidate / one auditor invocation.
5. Execute `python -B candidate.py --dir .` exactly once; preserve `candidate.json` and output.
6. Execute `python -B audit.py --dir .` exactly once; preserve `AUDIT.json` and output.
7. Do not retry either formal command. Any runtime error or failed gate is recorded as a failed/stopped experiment with exact reason; correction requires a successor run/issue, not mutation of this run.
8. Add result, hashes, execution environment, and stop/limitation statements to one result commit; run construction tests once more on the complete package; open a PR referencing #8528. Merge only after checking base/head and mergeability; do not force-update a branch that moved concurrently.

## Formal run ledger (initially empty)

Formal candidate invocations: 1/1 (`CANDIDATE_COMPLETE rows=22 cases=8`, exit 0). Formal auditor invocations: 1/1 (`PASS_METHOD_SCOPED errors=0 mutations=7/7`, exit 0). Candidate raw result: `candidate.json`. Independent audit result: `AUDIT.json`. Detailed environment, timing, hashes, and scope limits: `RUN_RECORD.md`. Construction tests and their failures are recorded separately in `CONSTRUCTION_LOG.md`.
