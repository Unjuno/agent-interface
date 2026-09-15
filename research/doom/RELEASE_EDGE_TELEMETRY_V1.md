# Release-edge telemetry v1

Status: **SOURCE IMPLEMENTED / OFFLINE HELPER TESTED / NO LIVE AUTHORITY**

Task: `O3-PH48-G2-RELEASE-EDGE-001`  
Base: `bc21199ac1e22ac34decc9fa1a73190e402480ee`  
Branch: `research/release-edge-telemetry-g2-bc21199a`

## Purpose

The retained v38/v39 traces timestamp X11-synchronized key-down admission but do not timestamp ordinary key-up inside InputOwner. Source ordering can bound normal release, but it cannot provide an exact ordinary release edge or continuous hardware state.

This version adds **telemetry only**. It does not change cover/recovery policy, lease semantics, hold duration, or the retained v38/v39 sources/results.

## Design

New pure helper:

`research/live_control/release_edge_telemetry_v1.py`

New versioned DOOM backend:

`research/doom/doom_typed_release_backend_v2.py`

The backend continues to use the existing `InputOwner v10`. For each ordinary keyboard release it records only two cheap caller-side monotonic timestamps around the existing synchronous `owner.call('up', ...)`:

1. `release_call_requested_ns` immediately before the call;
2. `post_sync_call_return_ns` immediately after the call returns.

`InputOwner v10` executes XTest KeyRelease and `d.sync()` before the call can return. Therefore the second timestamp is a conservative **post-sync upper edge**. It is deliberately not named the exact internal sync timestamp because thread/event scheduling can delay caller wakeup.

For a multi-key chord, the backend does **not** query X11 or emit telemetry between individual releases. It first completes every existing key-up call. Only when the backend-held set becomes empty does it:

- issue one `query_keymap()` on a dedicated read-only X11 connection;
- timestamp the sample start and finish;
- report which just-released keys, if any, are still down in the sampled X-server state;
- emit one aggregate `ordinary_release_telemetry` event bound to program `id` and `step`.

This avoids turning measurement into a deliberately staggered multi-key release.

## Evidence semantics

The new receipt establishes:

- a release-call request time;
- a bounded time by which InputOwner's release call has completed after its internal X11 sync;
- a later independently queried X-server key-state sample;
- program/step provenance.

It does **not** establish:

- the exact nanosecond of InputOwner's internal `d.sync()`;
- hardware switch state;
- application semantic consumption;
- independently useful task effect;
- any recovery-policy benefit.

The wording must remain **X11 release-edge telemetry / X-server state**, not “exact physical occupancy.”

## Perturbation analysis

The two monotonic clock calls around each existing release are the only work added between individual key releases.

The heavier operations—keycode lookup, one `query_keymap()`, result construction, and event publication—occur only after the final backend-held key is already released. Therefore they should not extend the commanded key hold itself.

They can, however, delay the inherited post-release final observation and add X-server load. A live/formal allocation must not be authorized until a development validation measures that perturbation and verifies that the telemetry event itself cannot renew authority or influence controller action selection.

## Offline checks

The pure helper logic was exercised in the authoring Python environment with seven deterministic cases:

1. release request/return bracket;
2. selected-key bitmap decoding;
3. two-key batch performs one state sample after both releases;
4. nonempty post-release state remains a failure observation rather than being rewritten as success;
5. a sample timestamp preceding the last release return fails closed;
6. overlapping/nonsequential release rows fail closed;
7. release-call failure propagates and creates no success receipt.

Result: **7/7 PASS**.

The repository files were not executed from a fresh checkout in this session because the working container previously failed GitHub DNS resolution. No X server, DOOM, GUI, model call, OS-input action, or formal allocation was used for these checks.

## H / T / D / C / U

### H — falsifiable hypothesis

Caller-side post-sync return brackets plus one post-batch X11 keymap sample can reduce the ordinary release uncertainty materially without changing key-hold/recovery semantics.

### T — minimum validation

Before any formal experiment, run the versioned backend in a development-only X11 fixture and compare:

- existing v10 release behavior;
- telemetry v1 release call-bracket width;
- post-release X11 sample state;
- added time from final release return to inherited final observation;
- any failure/nonempty state.

Use a multi-key chord and a single-key hold. No planner/model call is required for this validation.

### D — decision

- **PASS instrumentation:** all release batches produce ordered timestamps, post-release samples are empty under the controlled single-input-actor condition, and added post-release delay is bounded/documented without changing hold duration or authority semantics.
- **FAIL:** telemetry is observed to delay a key-up, change lease/release behavior, hide a nonempty key state, or feed privileged information to controller action selection.
- **UNCERTAIN:** X11 sampling/clock behavior cannot be aligned to the retained runtime monotonic clock or the development environment differs materially from the target runtime.

Passing instrumentation does **not** pass the recovery-policy hypothesis.

### C — competing explanations / break modes

- caller wakeup latency may dominate the release-call bracket even though InputOwner's internal sync is fast;
- an external actor may press/release a key between release and the post-release keymap sample;
- the extra X11 query may perturb post-release observation timing;
- X11 server state is not hardware state and not application semantic effect;
- cancellation/expiry already has a stronger owner-side verified-empty path and must remain separately interpreted.

### U — uncertainty

Primary error sources are scheduling delay between InputOwner completion and caller return, keymap query duration, X-server scheduling, uncontrolled external input, and measurement perturbation. No numerical uncertainty is claimed before a real development validation.

## Next gate

This source change does **not** authorize a live experiment.

After independent source review, the smallest next action is one development-only X11 validation of telemetry perturbation. In parallel, the project still needs a timestamped independent useful-effect/progress oracle that is not delivered to the controller as privileged action-selection input.

Only after both measurement channels are frozen should a new, separately preregistered matched coast-vs-explicit-recovery allocation be considered. Existing v38/v39 allocation IDs remain immutable and must never be reused.
