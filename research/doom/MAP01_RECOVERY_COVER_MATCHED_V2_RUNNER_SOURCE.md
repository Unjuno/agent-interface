# MAP01 matched bounded-recovery v2 runner source

Status: **OFFLINE SOURCE CONSTRUCTION PASS; NO FORMAL/LIVE AUTHORITY**

Task: `O3-PH48-G8-RECOVERY-RUNNER-SOURCE-001`  
Base: `e947b9809a3449de837e45211a4cb416d990279a`  
Reserved allocation: `map01-recovery-cover-matched-live-v2-01`

## Purpose

This runner isolates the local continuation mechanism in real MAP01 without mixing in model quality. It uses the existing `session_map01_v13.py` measurement/scorer/release contract unchanged and makes **zero model calls**. The simulated slow planner is a frozen 600 ms delay provider in both arms.

This is intentionally narrower than frontier-model efficacy. If a later formal allocation succeeds, it can establish a causal mechanism/effect result in the frozen MAP01 block. It cannot by itself establish that a frontier model is better, faster, or generally capable in DOOM.

## Matched block

Every pair reloads the exact retained `map01-threat-contact-v2` fixture with seed `990619`, skill 1 and the same v13 session path.

Both arms first execute the same explicit prelude: `d` for 180 ms followed by an observation. This creates the prior admitted motor intent and a fresh source observation. The planner-wait window then begins from an explicit runtime-clock receipt.

### COAST_CONTROL

During the 600 ms planner delay, submit one bounded `coast` program. It has no input authority.

### BOUNDED_RECOVERY

Reuse only the immediately preceding admitted motor intent (`d`) as five 50 ms pulses with observations between pulses. The recovery program:

- is a new, separately admitted program;
- binds to the exact source sequence/capture;
- has a 400 ms authority lease, below the preregistered 1500 ms maximum;
- also expires when the source observation reaches 1000 ms age;
- cancels fail-closed if a typed observation is not fresh, health becomes unavailable, or health drops below source health;
- must end with a verified terminal release.

The planner-delay timer is independent of the fallback program. If a fallback remains active when the simulated planner returns, the runner cancels it before continuing.

## Counterbalancing

One future formal workflow executes one allocation containing three matched pairs in fixed counterbalanced order:

1. coast → recovery
2. recovery → coast
3. coast → recovery

Each arm starts a new v13 session from the same saved fixture. This controls simple arm-order effects without creating multiple GitHub formal allocations.

## Measurement

The runner does not infer key occupancy from accepted program lifetime. For the fallback program's `intent_token`, it computes interval bounds from retained `input_admission` and verified `input_release_transition` receipts:

- definite retained input: `input_ack_ns → release_call_started_ns`;
- possible retained input: `admitted_ns → release_call_returned_ns`;
- overlapping key/pulse intervals are unioned, not summed;
- both are intersected with the runtime-clock planner-wait window;
- no-retained-input lower/upper bounds are the window complement.

The independent scorer remains isolated in v13. Scorer JSONL is read only **after** the session terminates. It is never routed back to the controller or guard.

## Formal launch gate

The runner refuses to start unless a launch-owner receipt matches all of:

- schema `formal-allocation-global-owner-v1`;
- allocation `map01-recovery-cover-matched-live-v2-01`;
- workflow path `.github/workflows/map01-recovery-cover-matched-live-v2-01.yml`;
- one matching workflow-path run;
- current and owner branch `main`;
- `PASS_CANONICAL_GLOBAL_OWNER`;
- current run equals owner run.

No workflow with that path is created by this task. Therefore this source merge does **not** grant a way to consume the allocation. A future workflow requires its own exact-path lease and must retain live-04's allocation-global ownership, non-cancelling serialization, exact source pins and terminal-score audit.

## Decision pre-classification

The runner can only emit a pre-audit disposition. A future formal workflow must still apply the frozen v2 terminal-score agreement and full experiment audit.

- hard release/input/scorer failure → `FAIL`;
- recovery does not reduce the no-retained-input upper bound → `HOLD`;
- recovery reduces no-input time but produces no independent useful event → `HOLD_MECHANISM_ONLY`;
- recovery reduces no-input time but produces an independent negative event with no positive event → `FAIL`;
- positive independent evidence after continuity improvement → `PASS_CANDIDATE_REQUIRES_TERMINAL_AUDIT`.

The last label is deliberately not scientific PASS.

## Offline validation

Disposable container, CPython 3.13-compatible source:

```text
python -m py_compile map01_recovery_cover_matched_v2_runner.py test_map01_recovery_cover_matched_v2_runner.py
python -m unittest -v test_map01_recovery_cover_matched_v2_runner.py

11 tests PASS
```

Covered cases include canonical/global owner acceptance and rejection, duplicate/wrong-workflow fail-closed behavior, program/lease bounds, source-age expiry, health/staleness guard cancellation, interval-union arithmetic, coast zero-input bounds, verified-release requirement, mechanism-only classification, and harm classification.

No model, GUI, ViZDoom, OS input or formal allocation was used in these construction tests.

## H / T / D / C / U

**H.** Reusing the immediately preceding explicitly admitted motor intent under a fresh health guard can reduce bounded no-input planner-wait time in real MAP01 without stale input or release failure; whether this creates independently useful task effect remains falsifiable.

**T.** Three counterbalanced coast/recovery pairs from the exact same retained threat fixture, one GitHub allocation, zero model calls, fixed 600 ms delay provider, direct release telemetry and isolated independent scorer. Stop after the first retained allocation; no same-allocation retry.

**D.** Scientific disposition remains the frozen v2 preregistration. Continuity-only improvement is not PASS. The runner's pre-classification cannot override terminal-score or launch-integrity gates.

**C.** Repeating the previous direction may reduce idle time while being useless or harmful; the fixture may favor one direction; asynchronous capture can widen intervals; independent scorer events may remain sparse; a later model-integrated result can differ.

**U.** The mechanism block is one fixture/seed and uses a simulated planner delay. It measures local continuation causally but does not estimate general model-latency performance. Main error sources are interval censoring, session timing jitter, sparse independent events and fixture specificity.
