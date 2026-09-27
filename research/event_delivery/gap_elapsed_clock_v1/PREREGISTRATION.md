# Locally preregistered successor study: elapsed-time eligibility for missing-event notification

**State at freeze:** formal invocation 0; local construction complete. This is a LOCAL allocation, not a published/claimed GitHub successor. Remote Issue creation and publication are blocked because the exposed GitHub MCP tools are read-only, no `gh` is installed, and direct GitHub DNS is unavailable. Do not represent this document as a GitHub premeasurement registration.

Allocation: `local-gap-clock-20260922-01`. Intended additive path: `research/event_delivery/gap_elapsed_clock_v1/`. Intake and pre-freeze main: `b2457b746a6df06f6536585dfe2ab937aff639f4`. The exact path returned 404 at this commit; branch search for `gap` returned none. These are bounded checks, not an exhaustive reservation or ownership guarantee. No remote branch is created.

## Origin and integration boundary

Closed #916 and #926 distinguish contiguous event admission from notification about a missing predecessor. #926's third-observation rule explicitly does not establish elapsed-time notification. Open #3876 identifies this distinction as a limitation for a passive event inbox. This study tests the caller-visible notification boundary, not a new producer, watcher, inbox integration, action scheduler or automatic resynchronization.

The #742 source is retained verbatim with Git blob `1f4f83eb51e1af3fc915ace83f0a3a4da6dbd0a6`. Inserting the exact #916 contiguous check yields SHA-256 `7dbe43bc27ccc0d6f19b33c01e438aecd68c33753c512963d8697a426c5d35c6`, matching the historical #926 source-freeze comment. No predecessor files or outcomes are modified. The notification wrapper is independently implemented from the Issue specification; it is NOT claimed to reproduce the original #926 wrapper bytes.

## H — hypothesis and analytical reduction

A fixed three-observation rule is governed by observation count, not elapsed time. That follows from its definition and does not need an experiment. The residual tested here is whether, over real Python processes and retained SQLite state, replacing only notification eligibility with elapsed monotonic time preserves exact contiguous admission, pending content, explicit ACK, and idempotent notification while exposing the expected cadence dependence of the count rule.

The elapsed rule must never issue a notice before 80 ms from the first observation of the same gap. It issues a notice on the first subsequent poll at or after the threshold, not necessarily at 80 ms. An inactive consumer has no autonomous wakeup in either arm. A late predecessor arriving before the elapsed threshold should drain normally without an elapsed-arm notice. Genuine progress must reset the gap identity and timer; a later tail event must not reset the current head gap.

**80 ms is an arbitrary frozen diagnostic discriminator, not a proposed production default.** A notice means evidence of a persistent observed gap; neither arm is entitled to conclude that an event is permanently lost.

## T — fixed local allocation

Use the provided Linux x86_64 execution container, CPython 3.13.5, SQLite 3.46.1. Docker CLI/image identity and OrbStack are unavailable. This is not a Docker/OrbStack replication. No installs, network calls, provider/model calls, GUI, OS task input, credentials or shared runtime changes occur in the experiment.

Each case uses fresh private SQLite storage and two distinct exec'd Python processes, one producer and one consumer. The orchestrator orders commands through bounded JSON-line pipes and observes database contents independently before and after each command. This is an ordered process/clock experiment, not uncontrolled concurrent racing. Consumer time uses `time.monotonic_ns()` in one clock domain. Source startup and orchestration overhead are retained but not confused with first-gap-to-notice latency.

The admission, pending and ACK implementation is the exact reconstructed #916 source. Start with E3 retained, ACK through E2, pending capacity 2. Offer E5 while E4 is absent. Compare `OBS_COUNT_3` against `ELAPSED_80MS`.

Frozen total: **3 repetitions × 4 scenarios × 3 poll profiles × 2 policies = 72 fresh cases**, balanced arm order. Exact order and requests are in `schedule.json`.

Poll profiles (nominal milliseconds after the case scheduling origin):

- fast: 0, 5, 10, 20, 40, 60, 80, 100, 140, 180, 200, 240, 300;
- slow: 0, 60, 120, 180, 240, 300;
- paused: 0, 140, 150, 180, 240, 300.

Scenarios:

- `permanent`: E5 remains pending with E4 absent;
- `late40`: E4 offered nominally at 40 ms, then drain E4/E5 in order;
- `tail40`: E6 offered at 40 ms while E5 remains head;
- `new_gap`: E4 at 40 ms; following actual E4/E5 acceptance, explicitly ACK through E4; E7 at 180 ms then exposes missing E6.

At a nominal tie, offer precedes poll. Real request/reply, worker processing and observation timestamps determine interpretation. Sleep requests are not assumed to be exact. Before interpreting late-arrival results, require the actual E4 offer completion to precede the first-gap instant plus 80 ms.

Construction is excluded: 8 synthetic-clock unit tests, 8 separate `construction-01` cases and 11 copied-evidence corruption controls. All existing construction outputs are retained. Freeze the source, auditor, schedule, this plan and environment before the first local formal invocation. No post-outcome source/gate edits, discarded cases, retries, seed replacement or same-path reruns are permitted.

## D — decision and audit

`PASS_LOCAL_CLOCK_BOUNDARY_SCOPED` requires every scheduled case and ordered command; exact source/schedule/freeze bindings; two distinct worker identities and clean exits; exact independent reconstruction of all database snapshots, dispositions, notification identities and retained database bytes; zero implicit ACK advances, missing-predecessor acceptance, pending drops, synthesized events or authority escalation; normal late E4/E5 drain; stable replay of the same notice; reset after genuine progress and no reset after tail arrival; all elapsed notices at age >=80 ms and at the first eligible actual poll; no elapsed-arm notice in `late40` before arrival; and at least one count-arm permanent-gap notification below 80 ms and one at or above 80 ms across profiles.

All 72 late/new-gap exposure conditions must be auditable (only relevant cases have a late arrival). The standalone auditor must import neither candidate nor runner nor inherited model. After auditing unmodified raw data, it must reject all 11 copied-evidence mutations: missing case, missing row, duplicate request ID, boolean invocation count, boolean observation count, authority upgrade, altered receipt identity, implicit ACK advance, missing process exit, changed database byte, and missing JSONL LF. Source rehash after the run must be exact.

`FAIL_LOCAL_AUDIT_OR_GATE` means an observed contract/gate mismatch or raw audit discrepancy. Separate any scientific contract failure from insufficient/malformed evidence in the report. `HOLD_TIMING_EXPOSURE` means real scheduling did not expose the registered late-arrival condition. `STOP_LOCAL_EXECUTION` means source, process, clock transport, output or other infrastructure failed; retain all partial files, and do not rerun. A publication STOP is distinct from local experimental disposition. No component PASS closes #3876 or the repository roadmap.

## C — controls, constraints and competing explanations

Counting observations can deliberately react quickly, so a notice before E4 arrives is NOT a defect in #926's count-based contract. This study only rejects interpreting that count as a fixed time budget. Likewise, waiting until a future poll is not hard real-time delivery. Scheduling, Python startup, SQLite fsync, serialization and parent observation costs can affect actual times. Report descriptive samples and extrema, not statistical or general latency guarantees. Commands are ordered, not simultaneous; no probability of a race or independent distribution is estimated.

Keep all notification authority fields false. Gap evidence never executes #677 resynchronization, advances ACK, drops a higher event, grants an action lease or changes semantic intent. Explicit ACK is allowed only after actual E4/E5 progress in `new_gap`. No shared runtime modification or default change is proposed.

## U — unresolved

Live producer/presentation integration, external delivery/consumption acknowledgement, process restart persistence of timer state, crash/power-loss, system suspend semantics, cross-machine clock domains, real model-visible response, useful-feedback latency, token efficiency, and product benefit remain untested. One host, three repetitions, four authored scenarios and a finite corruption set cannot establish general reliability or auditor soundness.

## Exact commands

Run from this directory, in ordinary Python mode (not `-O`):

```sh
python -B run_study.py --schedule schedule.json --freeze FREEZE.json --out local-formal-01
python -B audit.py --root local-formal-01 --schedule schedule.json --freeze FREEZE.json --out formal_audit.json
python -B test_audit_controls.py --root local-formal-01 --schedule schedule.json --freeze FREEZE.json --out formal_controls.json
```

The first command consumes this local allocation exactly once. Auditing retained bytes is not a repeat of the experiment. Never use existing output paths for a new allocation.
