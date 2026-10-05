# V39 pending-planner invalidation handoff

This follows #8031/#7963 and #59. It adds deterministic pending-planner coverage to the actual V39 `main()` loop on main `d3a51bc4c962b223d05280225042b96a033df8bf` composed with existing #8031 head `bbdede97bf0ccfc1c3a0b6454422b402e8cf0b6f`. Main was merged without conflicts. Production code is unchanged from that existing repair; this turn adds regression coverage and evidence.

H: a health-only invalidation received while a planner Future is incomplete must request interruption of that same turn, cancel its cover, verify neutral release, discard its dependent answer, and use a corresponding fresh frame before another plan. T: actual local ThreadPoolExecutor/Future held behind Events, scripted session rows, production monitor factory/selector/compiler/wait/cancel/frame barrier/final admission. D: reject stale/wrong-binding frames and reject replanning for unverified/nonempty release; a late completed active answer must gain no input authority. C/U: the reader, process and planner transport are doubles. No pixels, real provider interrupt, physical input, game, task effect, resource/performance or latency claim.

## Source of the observation

Health-only `ObservableSignalPolicyMonitor` consumes full `observation` rows; this is not a typed-observation delivery test. The extraction double gives health 90 at source, 60 at the invalidating frame, or raises unreadable-health for the UNKNOWN case. The authored-style nonfire cover and health envelope are fixtures, not a measured model-authored policy.

The invalidating full frame initially becomes latest. A higher-sequence frame with a different binding then overtakes it while cancellation waits for the terminal. After verified release, the production frame barrier must reject that latest frame and a same-binding higher-sequence frame with an older capture time, then accept the matching fresh frame. This exercises delayed qualification without changing monitor event registration.

## Retained executions

- `pending-v1`: 3 methods / 5 schedules pass. This first construction had an active nonempty answer checked only by `validate_action`; its immediate-action validity fields were incomplete. Retained as a narrower fixture result, not evidence of an otherwise admissible answer.
- `pending-v2`: corrects those validity fields, uses an exact geometry binding, explicitly builds the active answer contract, and checks the frame returned by the barrier. All 3 methods / 5 schedules pass.
- `red-current-main`: same v2 test, replacing only `observable_signal_guard_v2.py` with its exact main source. HARD and UNKNOWN schedules both error at missing invalidation observation identity. The three bad-release schedules still stop before that barrier. This is a source-toggle regression control, not a complete untouched-main run: #7963's frame barrier remains part of the composed controller.
- `focused-current`: repair restored; all 19 focused monitor/controller methods pass, with five retained pending schedules. The tests prove the Future is incomplete at invalidation/interrupt; the late completed active answer remains discarded. Unverified release, a remaining key, and a remaining button each stop with one planner call, no frame-barrier entry and no next cover submission.

`focused-review-repaired` records the final 19/19 run after separate review strengthened the active-answer binding assertion from schema/self-consistency to the literal expected source binding. All five final traces and the final test snapshot are retained. Earlier results are unchanged.

No method counts are added as independent samples. Local test durations are not controller latency measurements. The RED source and restored source are preserved. The v1 source snapshot was reconstructed by reversing the small v2 fixture edit and verified against its original pre-run SHA-256 before preservation; no v1 rerun was performed.

The selected 27-file source closure differs from the prior #8031 head only in this test module. The previous 40-test adjacent result therefore remains source-applicable (its local result was `Ran 40 tests ... OK`); it was not rerun. Focused checks were rerun because the shared test fixture changed. Syntax and proposal-scoped whitespace checks pass.

## Reproduce

From a checkout containing this package, with its existing Python dependencies:

```sh
python research/doom/pending_invalidation_59_e0cc_20261005/run_regression.py /new/output/path
python research/doom/pending_invalidation_59_e0cc_20261005/run_regression.py /another/new/output/path focused
```

The portable wrapper adjusts path/runtime setup and propagates the child test exit code, is guarded against import execution, and was syntax checked; retained runs used `original-runner.py.txt`. The original recorder exits normally after saving each result, so its authoritative test outcome is the subprocess exit code in `receipt.json`, not the recorder exit code. Every output directory and trace file is write-once. The runner starts only local Python test threads; no backend or model is launched. First logs, receipts, traces and exact source snapshots are retained. Public copies replace only private path prefixes and ephemeral fixture-root paths; `publication-provenance.json` binds original/public bytes. Receipt log hashes name the private originals; the public manifest names the normalized copies.

## Integration boundary

This is synthetic controller orchestration evidence, not a live threat-control result or an authorization to use the unassigned #59 game lane. The first planner result deliberately completes after a synthetic interrupt request while still marked eligible, testing rejection of a late answer; this does not establish real provider cancellation semantics. The fake terminal is only a scripted neutral-release receipt, not physical release proof. Controller failure cleanup is replaced by a no-op fixture, so actual failure-cleanup behavior is outside this result.

The existing #8031 proposal now includes current-main composition and #7963's unchanged barrier in its ancestry. Earlier records stay untouched. No other author's branch is changed or closed, no main merge, no formal allocation replay. Content quorum and nonauthor exact-current-tree integration remain necessary; no technical review is counted as a vote.

## Independent raw audit

The existing separate bugbot agent audited all five final traces without rerunning the controller/tests. Its source-bound checks confirm pending observation and matching interrupt, late eligible active-answer discard (`REJECTED_POLICY_INVALIDATED`), no executor/input authority, terminal-before-barrier, and fresh-frame-before-next-turn. All three bad-release cases have one planner call and no barrier/replan. Original earlier/final audit scripts and results are retained separately.

The raw timeline names event/sequence but does not record each rejected frame's full identity; those rejection details rely on the exact fixture source plus the barrier's returned `fresh.png`, not a standalone raw candidate log. Bad-release cases stop before normal report serialization; their trace still records the injected release, commands and no replan. These limits are also in the audit result.

`independent-audit/audit_readback.py /new/result.json` is a path-adjusted, import-guarded version of the final raw auditor with write-once output. It was executed against the normalized publication copies; all five cases pass. The retained `public-copy-audit.json` identifies those public trace hashes. This is an artifact readback, not another controller/candidate run.
