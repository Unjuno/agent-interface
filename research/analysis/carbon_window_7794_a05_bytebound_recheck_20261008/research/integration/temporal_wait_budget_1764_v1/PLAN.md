# Caller wait budgets versus event-time completion

Allocation: `temporal-wait-budget-1764-20260922-01`.
Publication: BLOCKED_GITHUB_WRITE. This is a **local pre-execution freeze**, not a GitHub preregistration. Proposed successor to open #22 and closed #1764; no successor Issue has been created. Keep both issues and all existing outcomes unchanged.

## Intake and additive scope

Intake main `d8358f6aa0211c660a0bd7c005174cb100e5eaad`. GitHub MCP inspected main, README, docs/CURRENT_GOAL.md, ROADMAP.md, recent open/closed Issues, open PRs, 100 returned branch names, #1764 and #22, and exact monitor source. Branch collection is paginated and not claimed exhaustive. Targeted temporal+silence/deadline, temporal+watermark and #1764+timeout searches did not return this experiment. Unpushed/unindexed work remains unknown.

Only `research/integration/temporal_wait_budget_1764_v1/**` is owned locally. Proposed branch `research/temporal-wait-budget-1764-20260922` is local only; remote creation is unavailable. The artifact repository is NOT a full clone or a descendant of upstream main. Intake SHA is provenance, not a claimed local ancestry relationship.

#1786's X11 PropertyNotify transfer, #3942/#3956's XTerm history study, #3983's panel captures, #3985's reader cost, #926's gap-notification timer, and other passive-reader/LoRA/abort allocations are not run or modified. Previous chat-local typed-endpoint evidence is preserved and is not pooled with this allocation.

## H — falsifiable claim

A consumer's bounded wait timeout is not evidence that its source event-time obligation failed. A source can emit B within the allowed interval after A while the relay delays B beyond the caller's waiting budget. Feeding the consumer clock as a fabricated empty source fragment into the exact #1764 AB monitor can then irreversibly report EXPIRED even though the complete source trace satisfies AB. A later watermark with a missing sequence has the same completeness problem.

A bounded adapter that preserves source times, validates a contiguous session/producer prefix and reports TIMEOUT_UNRESOLVED separately must return valid positive/negative source outcomes for complete prefixes, abstain on missing prefixes, and never change a one-shot timeout into a later success. No result grants authority or task success. This is adapter research, not a defect allegation against the historical finite-stream monitor.

## T — minimal executed boundary

Provided Linux x86_64 container, CPython 3.13.5, standard library only. No Docker/OrbStack executable or pinned image identity, no network experiment, package installation, model/provider call, GUI/X11/input, user file or external side effect.

One fresh source process and consumer process per case communicate through bounded JSON-line pipes and a foreground relay. Source generates its own real monotonic timestamps and sequence numbers. The relay may withhold exactly the registered record; it never changes event times. Both source and consumer are ready before A. Three shadow policies share the same delivered stream in the consumer: unchanged EVENT_ONLY monitor, SYNTHETIC_TIMER monitor, and BOUNDED_PREFIX candidate. They are not independently timed performance arms.

Six scenarios, three repetitions each, cyclic scenario-order rotation: 18 cases, 36 source/consumer processes. Case order is frozen in study.py. Construction has one separate six-case matrix and is excluded.

| Scenario | Generated / delivered source records | Expected candidate |
|---|---|---|
| TIMELY_B | A then timely B, both delivered | SATISFIED |
| SILENT | A only; source remains alive at wait timeout | TIMEOUT_UNRESOLVED |
| TIMELY_DELAYED_B | B generated on time; delivered only after actual caller timeout | TIMEOUT_UNRESOLVED, never reopened |
| LATE_B | B generated after event deadline but delivered within caller budget | EXPIRED |
| WATERMARK | complete A then an explicit source empty fragment after event deadline | EXPIRED |
| GAPPED_WATERMARK | timely B retained at source but omitted at relay; later seq3 watermark delivered | UNKNOWN_INCOMPLETE_PREFIX |

The source protocol defines a watermark as a monotonically advanced position in that single source's complete generated stream. It is not a generic promise made by every OS/application; the candidate requires all earlier sequence records. Source truth is evaluator-only. This is an authored notification fixture, not the real GUI producer or #22's same-model Calc evaluation.

A synchronous launcher has a 25 s allocation envelope; child command waits and cleanup waits are 2 s. An external tool call uses a longer 35 s envelope. Any timeout/source/process failure preserves partials and STOP; no rerun, continuation, replacement, seed tuning or post-result scorer change. Each completed case is fsync-checkpointed. The launcher writes the actual child exit and source hash receipt. Any partial denominator prevents a full PASS.

## Parameter / variable table

| Symbol or field | Meaning (Japanese) | SI unit | Definition | Domain / assumptions | Type |
|---|---|---|---|---|---|
| A, B | 起点イベントと必要な後続イベント | 1 | Authored labels, not GUI success | Single source, one obligation | Categorical scalar |
| source_ns | 発生元が採番したイベント時刻 | s (stored integer ns) | time.monotonic_ns at source emission | Same kernel/domain; nondecreasing | Integer scalar |
| delta_ns | AからBまでの許容期間 | s | 0.080 s; 80,000,000 stored ns | Closed upper bound | Positive integer scalar |
| budget_ns | 呼出側が待つ時間 | s | 0.160 s after consumer receives A | Distinct from event deadline | Positive integer scalar |
| deadline_ns | 呼出側の待機終了時刻 | s (stored integer ns) | A-receive time plus budget_ns | Not a source watermark | Integer scalar |
| sequence | 発生元の通し番号 | 1 | Starts at 1, advances once per source emission | Exact integer, not JSON Boolean | Integer scalar |
| SLACK | 実験の観測応答許容超過 | s | 0.150 s after caller deadline | Diagnostic host-scheduling allowance | Positive integer scalar |
| n | 正式な新規ケース数 | 1 | Six scenarios, three repeats | Exactly 18; no old rows | Integer scalar |

Dimensional check: event-time differences and delta are both durations stored as integer nanoseconds. Caller duration comparisons use the same representation but different endpoints. No server/remote clock is converted or assumed equal to this kernel clock. Unit resolution is not timer accuracy.

## D — fixed gates

PASS_CALLER_BUDGET_EVENT_TIME_BOUNDARY_SCOPED requires all 18 exact schedule rows, 36 source/consumer exits 0 with no forced cleanup/errors, source/packet/PID/session/sequence/clock lineage, unchanged upstream blob, all eight unit tests and at least twelve rejected semantic evidence mutations, and a separate raw-only audit with no errors.

Expected candidate totals: SATISFIED 3, EXPIRED 6, TIMEOUT_UNRESOLVED 6, UNKNOWN_INCOMPLETE_PREFIX 3. Zero false event-time expiration or unsupported success. SYNTHETIC_TIMER must yield false EXPIRED against the complete source in all three delayed-B and all three gapped-watermark cases; its three silent expirations remain unsupported, not proved false. EVENT_ONLY must remain PENDING at the silent wait boundary. Candidate timeout leaves its source monitor PENDING and adds zero source ticks. Late records do not reopen the caller result. All observed candidate return times must be no later than caller deadline plus the 150 ms slack. No hard-real-time claim follows.

Complete contradictory behavior is FAIL/HOLD at the relevant scientific gate; incomplete/source/provenance/exit/audit evidence is STOP/HOLD. The auditor's combined HOLD code must be interpreted with raw errors, not automatically as a scientific failure. Integrity PASS and unsafe-comparator FAIL are reported separately.

## C — analytical boundary and alternatives

At the caller deadline two worlds can share the same received prefix A: one generated no B, the other generated timely B whose notification is delayed. A decision using only that prefix and local elapsed time has identical inputs in both worlds. Declaring source failure in both is incorrect in the second world; declaring success in both is unsupported in the first. Therefore timeout alone permits only a waiting-budget result or uncertainty, unless an extra source completeness/delivery-bound premise is supplied. This is a direct indistinguishability argument, not a new distributed-systems theorem.

Contiguous source watermark evidence supplies the missing premise for this one trusted stream. A watermark after a sequence gap does not. An event-only monitor may deliberately remain pending; its finite-trace contract is unchanged and not accused of promising an external wall-clock service. A real system with guaranteed bounded delivery may support stronger expiration semantics. The present fixture has no such bound.

## U — unknowns and limits

No physical GUI effect, model consumption, cost/token saving, natural failure frequency, hard real-time, suspension/clock migration, multiple producers, authenticity, crash durability or production promotion. The repetitions are deterministic exposures, not independent natural-race samples. Timer lag is descriptive only; CPU frequency/host load are not controlled, so no calibrated combined uncertainty or coverage factor is asserted. A separate auditor means independent implementation/process, not an independent researcher.

## Roadmap / stop boundary

Source reconstruction -> excluded units/construction -> local source/environment/gate freeze -> one 18-case process allocation -> independent raw audit and semantic corruption controls -> retain source/raw/report/patch -> GitHub Issue/PR publication only if write operations become available -> exact-head review/checks/main readback -> only an owned merged branch may be deleted after dependency checks.

Broad ROADMAP.md, #22 and integrated same-model benefit remain open. Publication failure does not authorize new experiments merely to make the backlog grow.
