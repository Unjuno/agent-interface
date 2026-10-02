# Result — Issue #5951 host-only finite method construction

## Disposition

**METHOD_PASS_SCOPED after explicit auditor and comparator successors; allocation 01's `FAIL_RAW_AUDIT` remains retained.** The candidate was executed once on the original eight frozen cases. The corrected independent auditor in successor 02 matched all eight candidate decisions and exact error sets. A stronger static clause-to-targeted-test baseline was then separately constructed: successor 04 matched all eight outcomes, and an independent raw-table auditor passed against the exact baseline-output hash. It passes exact copy, paraphrase, and explicit UNKNOWN; it rejects omission, weakened condition, unsupported addition, legitimate authenticated supersession, and bad source span. The source-aware candidate passes the legitimate supersession and UNKNOWN controls while rejecting the four corruption/omission classes. Five unittest methods pass, including omission, weakening, invented permission, equal-turn supersession, bad-span, and forced-ambiguity mutations.

The discriminating result is narrow: **in this authored finite representation**, preserving each clause's atoms with static trace/test coverage is insufficient to retire an earlier prohibition after a later authenticated superseding turn. An explicit authenticated precedence relation permits that case without weakening other clauses. This is a method/construction result, not a live agent or language-understanding result.

## Retained allocation history

1. `host-t0-01`: candidate run returned the intended pass/fail directions. Five unit-test methods passed. Independent auditor v1 returned `FAIL_RAW_AUDIT` on two cases because it expected only one error class where the candidate correctly reported two simultaneous findings. Preserve [`candidate.raw.json`](candidate.raw.json) and [`audit.raw.json`](audit.raw.json) unchanged.
2. `successor_02`: corrected only the auditor's two expected error sets and audited the exact SHA-256-bound candidate output without rerunning it. Result: `PASS_RAW_AUDIT`, 8 cases, no errors.
3. `successor_03`: the strengthened static comparator's retained rows reveal it wrongly failed a correctly linked UNKNOWN ambiguity. The script exited 0 because its output writer did not enforce the declared UNKNOWN acceptance rule; classify this as `FAIL_SPEC_REVIEW`, not a script-reported failure. Preserve its raw rows unchanged.
4. `successor_04`: corrected only the baseline's UNKNOWN rule; result `PASS_BASELINE_CONSTRUCTION`, zero mismatches. The baseline still rejects legitimate supersession because it retains the earlier source clause as a test obligation.

## Scope and limits

No Docker container ran: the Docker Desktop context was visible, but the daemon query hung and was stopped before inventory/ownership could be established. No unknown container was touched. This is host-only deterministic METHOD evidence, not a container T0. Atoms and labels are hand-authored; the test does not assess paraphrase extraction, ambiguity adjudication by humans, a model, authenticated transport, a production contract pipeline, action authority, safety, downstream effects, or task outcomes. No runtime or product promotion follows. A separate empirical T1 with independently adjudicated task instructions remains necessary to test the extraction problem.

## Reproduction

From this directory, Python 3.12.10 standard library only:

```powershell
python experiment.py
python -m unittest -v
python successor_02/independent_audit_v2.py
python successor_04/static_trace_tests_v3.py
python successor_04/audit_baseline_v3.py
```

The first candidate execution was single-shot. Later candidate command invocations were not made; the final test/audit commands are verification of frozen artifacts. Frozen inputs and outputs are SHA-256-bound in the allocation `FREEZE.json` files and `RUN.json`.
