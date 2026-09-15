# MAP01 release telemetry candidate v2 — non-staggering correction

Status: **SOURCE REPAIR IMPLEMENTED / OFFLINE LOGIC PASS / LIVE INTEGRATION NOT AUTHORIZED**

Task: `O3-PH48-G3-RELEASE-TELEMETRY-V2-001`  
Base: `73b1b685737e6cc258b5eeab39b8111668d6971f`  
Branch: `research/release-telemetry-v2-73b1b685`

## Why v2 exists

The retained v1 candidate correctly avoided a **pre-release** state probe, but source review found a multi-key perturbation that its single-key Xvfb probe could not detect.

`input_transition_owner_v1.InputOwner.call('up')` performs:

```text
v10 up -> d.sync -> input_state -> return telemetry
```

and `doom_retained_input_backend_v1.raw()` invokes that wrapper once per key. A two-key release therefore becomes:

```text
up key 1 -> d.sync -> input_state round trip -> publish
up key 2 -> d.sync -> input_state round trip -> publish
```

instead of the historical back-to-back release loop. The first v1 result remains retained; it is not overwritten or relabelled. Its 500-trial Xvfb result is still valid for the **single-key queued release primitive** at its stated scope. It does not validate the multi-key integration.

## v2 repair

### `input_transition_owner_v2.py`

For explicit `up` / `button_up`, the wrapper now performs only:

1. caller monotonic timestamp;
2. unchanged InputOwner v10 release call;
3. caller monotonic timestamp;
4. return a receipt.

It performs **no `input_state`, keymap query, callback, or telemetry publication inside the per-input release call**.

The receipt also snapshots cheap local lease state at request time:

- deadline still valid;
- cancellation already requested or not;
- focus already invalid or not;
- `ordinary_release_candidate` derived fail-closed from those conditions.

This prevents known cancel/expiry/focus-invalid cleanup releases from being silently promoted to ordinary release measurement.

### `doom_retained_input_backend_v2.py`

The adapter buffers release receipts in the executor-step thread. While any backend-held key remains, it performs no state query and emits nothing.

After the final backend-held key release returns, it performs exactly one `input_state` sample, verifies aggregate owner bookkeeping, sample ordering and owner identity, annotates all buffered receipts, then publishes them. Existing direct analyzer v1 can still consume the per-key `input_release_transition` records because their event/token/key/release-clock contract is retained.

The crucial two-key operation order is therefore:

```text
up key 1
up key 2
input_state
emit key-1 receipt
emit key-2 receipt
```

not:

```text
up key 1
input_state
up key 2
```

The executor-step wrapper also removes its thread-local telemetry context after the step returns; an incomplete/raising release path cannot leak a partial receipt batch into the next step.

## Remaining measurement scope

V2 still does **not** claim an exact internal InputOwner `d.sync()` timestamp. `release_call_returned_ns` is a conservative post-sync caller timestamp and includes possible worker/caller scheduling wakeup latency.

The one post-batch `input_state` verifies owner bookkeeping, focus/pointer state and timing from InputOwner v10. It does not continuously query physical keyboard state and must not be described as hardware occupancy or application semantic effect.

A concurrent, disjoint line landed after this branch BASE on main at `64b286722adaf4daae8936cc373d44c559bd86da`: `O3-G2-INDEPENDENT-PROGRESS-CLOCK-001` retains a scorer-only independent-progress event contract with 14/14 contract tests. That closes the **event vocabulary** gap but explicitly leaves ViZDoom/session isolation and polling integration unproven. This v2 task does not touch that lane.

## Offline validation

Two deterministic suites are added:

- `research/live_control/test_input_transition_owner_v2.py` — 5 cases;
- `research/doom/test_doom_retained_input_backend_v2.py` — 8 cases.

The authoring Python environment exercised equivalent deterministic logic for the wrapper and two-key batch path successfully. The committed suites themselves were not executed from a fresh repository checkout in this session because the available container previously failed GitHub DNS resolution.

The tests require, among other cases:

- wrapper `up` performs no `input_state` call;
- cancelled/expired/focus-invalid cleanup is not an ordinary candidate;
- two-key release has no sample or emit between key-ups;
- one aggregate sample verifies the whole batch;
- nonempty owner state fails closed;
- post-batch sample ordered before the final release return fails closed;
- owner-identity mismatch fails closed;
- backend-unowned release fails closed;
- key-down admission behavior remains preserved.

No X server, DOOM, model call, GUI action or formal allocation was used for this v2 source repair.

## H / T / D / C / U

### H — falsifiable hypothesis

Release telemetry can bracket ordinary key-up without materially changing the historical ordering/duration of a multi-key release batch.

### T — minimum validation

Before MAP01 or any formal model allocation:

1. execute both committed deterministic suites;
2. run a development-only Xvfb probe containing at least single-key and two-key chords;
3. retain operation order proving no state query/publication occurs between chord releases;
4. measure per-call bracket width and the added delay **after the last release** caused by the one aggregate sample/publication;
5. include stale cancel/expiry cleanup so it remains measurement-invalid.

No planner/model call is needed.

### D — decision

- **PASS source repair:** deterministic tests pass and code review confirms `up, up, sample, publish` for a two-key chord.
- **PASS development instrumentation:** Xvfb/target-X11 development probe verifies all chord keys released, no between-release sample, and bounded documented post-release overhead.
- **FAIL:** any telemetry work is observed between individual chord releases, stale cleanup is accepted as ordinary measurement, or the adapter changes lease/hold/recovery semantics.
- **UNCERTAIN:** target MAP01/X11 behavior cannot be reproduced or the caller bracket is too wide under load.

Passing these gates still does not authorize recovery-vs-coast efficacy testing.

### C — competing explanations / break modes

- caller wakeup latency can widen the release bracket even with unchanged X11 release;
- an asynchronous owner release may occur before explicit cleanup; v2 rejects known cancel/expiry/focus-invalid cases but other unobserved release paths remain a review concern;
- the aggregate post-release sample can delay the final observation even though it no longer delays another key release;
- owner bookkeeping is not a physical keyboard bitmap and not task usefulness.

### U — uncertainty

Primary remaining uncertainty is development/runtime integration under real X11 capture load, post-batch sample overhead, progress-clock session integration, and independent useful-effect timing/cadence. No population or hard real-time guarantee is claimed.

## Product Hunt consequence

The PH-worthy story should not be “we made a timer faster.” The defensible visual is a synchronized timeline showing:

```text
planner still thinking
│
├─ authorized local input delivered
├─ ordinary multi-key release completed without measurement-induced staggering
├─ stale/cancelled authority rejected
└─ independent useful effect observed
```

V2 addresses the release-observability line. The independent progress **contract** now exists on main, but safe scorer/session integration remains a separate gate before the final synchronized demo can make that last line a live claim.
