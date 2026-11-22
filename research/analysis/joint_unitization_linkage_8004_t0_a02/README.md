# Issue #8004 — joint unitization/linkage uncertainty, T0 A02

## Scope and planned decision

This is a finite, authored method test for whether alternative event boundaries and alternative cross-channel link assignments can interact in a channel-overlap diagnostic. The endpoint is `H2+`: the number of reconstructed event components observed in at least two of four channels. The preregistered threshold is 3. The issue's H gate is an existence claim in this fixture: each one-factor sensitivity range stays on one side of the threshold, while the joint range crosses it and must be reported `UNIDENTIFIED`.

Linkage alternatives are finite assignments, not probabilities. No likelihood/posterior is estimated. No capture-recapture population size or all-channel-unobserved count is estimated; the oracle's known all-zero event is truth-only and must not be promoted as an estimate.

## Authored fixture

`public_input.json` contains a clean unique-ID control and two matched joint-ambiguity scenarios with four channels each: separate source roots versus a shared A/B source root. Raw intervals include two nearby A records that can be merged or split, matched B records, a stable AC event, heterogeneous channel capture patterns, two temporally overlapping but distinct B/C events, an A event aligned with a D telemetry gap, and a right-censored D record. `auditor_truth.json` separately maps the records to ten latent opportunities, including one event with no channel detections. The candidate never reads this truth file.

Each joint scenario has four frozen combinations: merged/split segmentation crossed with hard/alternate linkage. The boundary-only set holds hard linkage fixed; the linkage-only set holds merged segmentation fixed. Both one-factor envelopes are `[2,2]`; the joint envelope is `[2,3]` and crosses threshold 3. The clean unique-ID control reconstructs its oracle `H2+ = 3` exactly and is not flagged.

## Audit and mutation gates

The independent auditor does not import candidate code. It reconstructs linkage components through exhaustive subset enumeration with a one-record-per-channel component constraint, validates raw-record/oracle coverage and missing/censored status, and independently recomputes every capture-history histogram and envelope.

Six mutations must fail closed: force consensus segmentation, delete a plausible match, add a known false match between overlapping distinct events, count a split as extra independent failures, drop the censored opportunity, and label an `UNIDENTIFIED` envelope as zero unseen events. These test only this finite authored protocol.

## Execution control

After `FROZEN.json`, run only:

```sh
python3 -B run_formal.py
```

The driver creates `formal_started.json` with exclusive-create semantics before any CLI call, verifies all frozen source hashes, invokes candidate once and auditor once, captures outputs, and writes `terminal.json`. A second driver entry fails before launching the candidate. Do not invoke `candidate.py` or `audit.py` directly after freeze and do not retry a failure.

The expected runtime is CPython 3.14.5 on macOS arm64, standard library only, native CPU. No model, GUI, network, user data, shared container, or external effect is required. See `FROZEN.json` for exact source/input hashes and `terminal.json` for invocation counts, exits and derived hashes.

## Limits

The fixture's segmentation/linkage alternatives are authored, not empirically calibrated. Passing establishes only that this enumerator and auditor preserve uncertainty and detect the six planted corruptions. It does not establish realistic error distributions, independence assumptions, natural failure ascertainment, a production failure count, or safety. Any real-trace T1 requires a separate source-bound continuous trace and independent annotation/identity adjudication.
