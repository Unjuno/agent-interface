# MAP01 v38/v39 useful-control retained reconstruction v1

Status: **SOURCE CLOSURE + ANALYZER IMPLEMENTED; RETAINED-DATA EXECUTION NOT RUN IN THIS SESSION**

Task: `O3-PH48-W1-USEFUL-CONTROL-001`  
Base: `bc21199ac1e22ac34decc9fa1a73190e402480ee`  
Branch: `research/useful-control-g2-bc21199a`

This successor narrows the r133 proxy. The prior posthoc analysis measured accepted-program envelopes. That is useful for answer/program liveness but can count a mixed hold/coast program as motor-capable for its whole lifetime. This report defines a conservative held-input measurement that uses retained X11 acknowledgement and frozen source ordering instead.

No v38/v39 allocation is rerun. Existing raw results and preregistrations remain immutable.

## Result class

**REPAIR / PARTIAL MEASUREMENT CLOSURE.**

The retained v38/v39 evidence is sufficient to reconstruct bounded X11-acknowledged held-input coverage for normally completed keyboard holds. It is **not** sufficient to reconstruct an independently verified physical keyboard bitmap at every instant or a timestamped independently scored first useful task effect. Therefore the scientific P0 is narrower, but not yet closed.

## Proven from retained events and retained source

1. Both retained runs contain per-key `input_admission.input_ack_ns` and per-hold `keys_held.input_ack_ns` receipts. `keys_held` occurs only after all requested key-down calls have returned from the X11 input-owner path.
2. In the frozen hold implementation retained with v38 and v39, a normal hold executes in this order:
   - key-down calls and X11 synchronization;
   - `keys_held`;
   - one or more observation captures while the hold loop is active;
   - key-up calls in `finally`, each synchronized through the input owner;
   - one final observation capture;
   - `step_completed`.
3. Therefore, for a normally completed hold, the release transition is bracketed by the penultimate and final exact observation capture timestamps for that `(program id, step)`.
4. Early cancellation/revocation is different. The independent input owner can observe the cancellation bit and release before the reader publishes `cancel_requested`. Consequently `cancel_requested.requested_ns` is **not** a valid strict release lower bound. A verified-empty `input_released.owner_release.verified_ns` remains a valid upper bound.
5. The retained independent DOOM scorer exposes final kill/death/map-exit state. The retained controller-visible typed stream exposes health/ammo. Neither is a timestamped independent oracle for the **first useful task effect**. Viewport pixel change is also not such an oracle.

Relevant retained source closures inspected at their retained commits include:

- v38 retained source: `540d542190c4b31554128649a6e86597a1e5fb36`, `research/live_control/session_v4.py`;
- v39 retained source/result: `ebb8c7837edf86cc9d02c60bec58828e45fb6c77`, including `session_v7.py`, `session_v8.py`, `input_owner_v10.py`, the DOOM typed backend stack, and the retained runtime source manifest.

## Measurement contract

For each planner-wait interval and each declared `cover_program_id`:

### Held start

Use `keys_held.input_ack_ns` as the conservative start at which all requested keyboard downs have passed the X11 synchronized input path.

This is stronger than accepted-program time but is **not** relabelled as a continuously sampled physical keyboard state.

### Normal completed hold release

For a hold with `step_completed`:

- release lower bound: penultimate exact observation `capture_ns` for that `(id, step)`;
- release upper bound: final exact observation `capture_ns` for that `(id, step)`.

The frozen source orders key-up synchronization between those two captures.

### Interrupted hold release

For an interrupted hold:

- positive-duration lower bound: none beyond the acknowledged held start;
- upper bound: verified-empty early owner release if present, otherwise verified terminal release.

This deliberately widens uncertainty rather than treating reader-side cancellation publication as physical release time.

### Planner-wait output

The analyzer reports per decision:

- model wait;
- old motor-capable **program-envelope** coverage as comparator;
- X11-acknowledged held-input coverage lower bound;
- X11-acknowledged held-input coverage upper bound;
- no-held-input lower bound;
- no-held-input upper bound;
- the hold receipts and release-bracket basis used.

Intervals are unioned before duration calculation, so overlapping evidence cannot double-count coverage.

## Analyzer

New source:

`research/doom/analyze_map01_v38_v39_useful_control_v1.py`

Intended output:

`research/doom/results/map01-v38-v39-useful-control-posthoc-v1/analysis.json`

The output directory is fail-closed: an existing output path raises `FileExistsError` rather than silently overwriting an earlier reconstruction.

## Checks executed in this session

- Python AST parse: PASS.
- Synthetic normally completed hold: PASS; classified as `NORMAL_COMPLETION_SOURCE_ORDER` with a release bracket.
- Synthetic interrupted hold with verified-empty early release: PASS; classified as `INTERRUPTED_VERIFIED_EMPTY_UPPER_ONLY`.
- Synthetic overlapping interval union: PASS.
- Retained v38/v39 event excerpts: confirmed `input_admission` / `keys_held` receipts exist.
- Retained v38/v39 source ordering: inspected at retained commits.

### Not executed

The analyzer was **not run against the full retained result directories in this session**. The available local runtime could not clone GitHub because DNS resolution failed. No `analysis.json` is committed here, and no numeric held-coverage result is claimed from an unexecuted reconstruction.

An execution-capable Worker may run exactly this analyzer from this branch/base and retain the first output under the leased result path. It must not edit v38/v39 raw inputs.

## H / T / D / C / U

### H — falsifiable hypothesis

The old motor-capable accepted-program envelope materially overstates actual keyboard-held coverage during at least some planner-wait intervals, especially mixed hold/coast cover programs.

A second hypothesis is that the retained logs are sufficient to bound keyboard-held coverage without a new live allocation.

### T — minimum test

Run the analyzer once over **all** retained v38/v39 decisions, not a selected subset. Stop after every planner wait has either bounded held coverage or an explicit unavailable evidence state.

No model call, GUI action, OS input, or formal allocation is needed.

### D — disposition

- **PASS measurement reconstruction:** every relevant completed hold has the required held receipt plus held/post-release observation pair, and all interval invariants hold.
- **REPAIR:** held coverage is bounded but first independently useful effect remains unavailable, or a bounded instrumentation gap remains.
- **FAIL:** retained event/source ordering contradicts the proposed brackets.
- **UNCERTAIN/BLOCKED:** a required retained receipt is absent and cannot be bounded without inventing evidence.

Current disposition before retained-data execution: **REPAIR / PARTIAL CLOSURE**.

### C — competing explanations / break modes

- Accepted program lifetime may remain a good approximation for some pure-hold programs even if it overstates mixed programs.
- X11 acknowledgement is not the same claim as continuously sampled physical keyboard occupancy.
- A visually changing frame may be unrelated to useful progress.
- A final kill/map-exit score cannot localize which hold first caused a useful effect.
- Interrupted holds can have wider release uncertainty because the independent owner is deliberately asynchronous.

### U — uncertainty

Primary uncertainty sources are missing normal key-up timestamps, lack of per-sample keyboard bitmap receipts, asynchronous release ordering on interruption, clock/event publication latency, and absence of an independently timestamped useful-effect oracle.

No numeric confidence is fabricated.

## Smallest justified successor

If the retained-data execution passes the bracket invariants, the next instrumentation generation should add only what remains missing:

1. an owner-side timestamped input-state receipt that independently samples the relevant keyboard/button state without granting or renewing authority;
2. a scorer-side timestamped useful-effect event that is **not delivered to the controller as action-selection information**;
3. a matched, newly versioned coast-vs-explicit-recovery experiment only after those measurements are frozen and a separate formal lease is issued.

Do not rerun `map01-v38-integrated-threat-live-01` or `map01-v39-coast-liveness-live-01`.

## Product Hunt consequence

The highest-value 48-hour demo is not another opaque MAP01 retry. It is a legible timeline showing, on the same clock:

- slow planner wait;
- local input actually acknowledged/held;
- stale/invalid authority boundaries;
- verified release;
- independently scored useful effect.

If the system can visibly continue useful control while the planner is still thinking—and can visibly stop when authority becomes stale—that is a stronger and more defensible demonstration than a single lucky game clear.
