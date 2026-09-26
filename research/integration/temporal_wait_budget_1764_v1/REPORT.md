# Result: caller waiting budget is not event-time failure

**PASS_CALLER_BUDGET_EVENT_TIME_BOUNDARY_SCOPED**. One locally frozen allocation, 18 first cases, 36 source/consumer process exits 0, no forced cleanup, no formal rerun. **BLOCKED_GITHUB_WRITE** remains separate: this report, proposed successor and PR are not published to GitHub and nothing was merged by this worker.

## Main finding

A consumer that fabricates an empty source event at its local timeout can irreversibly report EXPIRED even though a timely B exists at the source. A later empty source fragment after a missing sequence can cause the same false inference. Keeping caller-budget termination separate from source-monitor state avoids these six directed false expirations and three unsupported silence classifications. This does not turn unknown outcomes into successful task completion.

| Scenario | Cases | Source trace truth | Synthetic-timer comparator | Bounded-prefix candidate |
|---|---:|---|---|---|
| TIMELY_B | 3 | SATISFIED | SATISFIED | SATISFIED |
| SILENT | 3 | PENDING at observed cutoff | EXPIRED, unsupported | TIMEOUT_UNRESOLVED |
| TIMELY_DELAYED_B | 3 | SATISFIED | EXPIRED, false | TIMEOUT_UNRESOLVED, not reopened |
| LATE_B | 3 | EXPIRED | EXPIRED | EXPIRED |
| WATERMARK | 3 | EXPIRED on complete source prefix | EXPIRED | EXPIRED |
| GAPPED_WATERMARK | 3 | SATISFIED in source trace | EXPIRED, false | UNKNOWN_INCOMPLETE_PREFIX |

The complete-source oracle is scoring-only. The candidate sees exactly the same delivered records as the two comparison monitors, with explicit session/sequence/type checks. No historical result is pooled. The upstream EVENT_ONLY monitor correctly remains PENDING when no source time advancement is delivered; it does not promise a wall-clock waiting service.

## H / T / D / C / U

**H.** Consumer timeout is not a source completeness certificate. Source-time evaluation plus a distinct caller wait result should separate real event-time expiration, unreceived timely success and incomplete prefixes.

**T.** Six directed scenarios, three cyclic-order repetitions each; one fresh source and consumer per case, real OS pipes and source monotonic timestamps. All three policies run as shadow interpretations in each consumer. Delta is 80 ms and caller budget 160 ms; they have different starting endpoints. Source advancement for late/empty-fragment controls is scheduled after 110 ms. Construction six cases and eight unit tests are excluded. Source/gates/environment/auditor were frozen locally before the one formal orchestration; there was no GitHub pre-execution registration.

**D.** All 18 frozen case gates passed. Candidate totals: SATISFIED 3, EXPIRED 6, TIMEOUT_UNRESOLVED 6, UNKNOWN_INCOMPLETE_PREFIX 3. Comparator false expirations: 6; silence classifications without sufficient evidence: 3. Raw-only audit errors 0; all 12 semantic evidence mutations rejected. No source changes, case replacement or formal retry after freeze. The scoped PASS qualifies this boundary result, not the unsafe comparison policy.

**C.** The relay deliberately withholds/omits records, rather than sampling natural transport failures. The source is a trusted single stream with complete sequenced emission, not an authenticated GUI/event producer. The candidate's event outcomes are historical notification results, not fresh action authority. Bounded-delivery systems may justify stronger statements, but this fixture makes no such assumption. Candidate abstention trades availability for not inventing source outcomes.

**U.** No GUI/model/task experiment, natural failure probability, delivery acknowledgment, broad parser robustness, cross-clock migration, authentication, power-loss durability, hard-real-time or product claim. This adapter is research-only and must not be installed as a production default. The externally supplied `now` is a trusted integer kernel-clock value in the exercised path; arbitrary calls with malformed `now` are outside the finite validation and not established safe. Independent audit means separate implementation/process, not an independent researcher. CPU frequency and host load were uncontrolled; no calibrated combined uncertainty or coverage factor is asserted.

## Analytical argument and unit check

At the caller timeout, two source histories can have the same received prefix: an A with no subsequent B, or an A followed by timely B that has not yet arrived. A decision using only that prefix and elapsed caller time receives identical inputs in both. Declaring source failure in both is false in the timely-B history; declaring source success in both is unsupported in the no-B history. Therefore a caller can stop waiting without deciding source success/failure. In this finite single-source fixture, a contiguous source fragment after the deadline supplies the missing time-progress/completeness premise; a sequence gap does not.

The complete parameter/variable table is in PLAN.md. All clock differences and thresholds use integer nanoseconds; subtraction and comparison are between durations in the same declared kernel domain. A 160 ms caller budget and an 80 ms source event allowance are not interchangeable despite sharing units. Nominal nanosecond representation is not a timing-accuracy guarantee.

Example from formal case 02: the source generated B 0.333 ms after A, within its 80 ms allowance. The relay delivered it 160.690083 ms after the consumer received A, after the caller timeout at 160.239741 ms. The candidate preserved TIMEOUT_UNRESOLVED; the event-only source interpretation later became SATISFIED. No late packet rewrote the one-shot caller result.

## Environment and observed timing

Provided Linux 6.18.44 x86_64 execution container, CPython 3.13.5, standard library only. CPU reports AMD EPYC 9V74, five exposed logical CPUs, eligible affinity 0-4. CLOCK_MONOTONIC is used by all three processes per case. The audit checks source and consumer timestamps against surrounding parent send/receive brackets. No Docker CLI, image/engine identity or Docker/OrbStack equivalence is claimed. No experiment networking, package installs, GUI/input or provider calls.

Total synchronous formal orchestration: 23.149067991 s, child exit 0 inside its 25 s safety envelope. This includes process startup and is not a policy-speed comparison. Six timer overshoots had median 0.2405145 ms, range 0.231613-0.304404 ms. These are descriptive observations only (one host, six timers, uncontrolled frequency/load); no tail-latency or hard-real-time guarantee follows. All observed returns met the frozen 150 ms maximum-slack gate.

## Provenance and retained validation

- Intake main: `d8358f6aa0211c660a0bd7c005174cb100e5eaad`.
- Final observed main: `cadb40fcd34803a96556faed3bb1e4843af061ba`; this worker did not update it.
- Exact upstream monitor Git blob unchanged at both: `c4c812b3e53917fd4ce102f14b689339d580ed20` (3501 bytes).
- FREEZE.json SHA-256: `1e8fcf459faf2fdcf3dd722d6198c982ea2559c356fb7aed5c13b489eb717fcc`.
- formal-01/rows.jsonl SHA-256: `8957bea3b40121c025c85cac93ae77497b947f0164c02c8b06548c8d4116e075`.
- AUDIT.json SHA-256: `c49b053ca2f2cecabb6e409825dae77f707778d9d1a528aa7d87314f8a48650d`.

`EXECUTION.json` contains the actual launcher command, exit, clocks and source hashes; `formal-01/` contains all source/consumer raw wire records, cases, exits and partial-safe consumption markers. Construction is separately retained. `POSTFORMAL_PROCESS_CHECK.json` records read-only /proc checks, never signals saved PIDs. Packaging verification is postformal and does not modify the frozen runner/auditor or any formal bytes.

Previous typed-endpoint experiment is preserved in the original supplied ZIP SHA-256 `f7ae6f6d707e3e558b07b154143918a45aeac09af9dc90cfac375ebb20164fb6`. Read-only reconstruction verifies 146 manifest entries and reproduces original audit and 12 mutation-control output bytes exactly, with zero new X11/formal invocations. See PREVIOUS_EVIDENCE_REAUDIT.json. That older result is neither pooled with nor replaced by this study.

## Revalidate, do not rerun the consumed allocation

From this directory, the following read-only commands re-evaluate retained bytes:

```sh
python -B verify_retention.py
python -B audit.py formal-01 --formal --mutations
python -B -m unittest -v test_policy
```

Do not invoke launch.py or study.py against the consumed formal output. A new empirical question requires a separately declared allocation, not removal of consumption markers. No historical formal.py is imported or executed by these commands.

## Integration decision and remaining roadmap

Retain as an observation/result contract constraint for #22/#2789. It is not a runnable production temporal service or a same-model task-benefit result. The next integration question is whether an existing real producer can supply a verifiable complete prefix and explicit time domain; without that evidence, use a waiting-budget outcome rather than source failure. Data-stream processing, distributed notification systems and GUI-agent recovery share this distinction, but no transfer to those systems has been measured here.

GitHub MCP currently exposes 48 read-only operations; issue/comment creation, file push, PR creation/merge and branch deletion are absent. The plugin directory returned the already-installed connector and gh CLI is absent. No mutation endpoint was invented or used. Proposed Issue/PR text and an additive patch are supplied for later publication with **retrospective/local-freeze** chronology clearly labeled. No remote successor, PR, merge, CI result or branch cleanup is claimed. #22, #1764's original disposition and the whole-repository roadmap remain unchanged.
