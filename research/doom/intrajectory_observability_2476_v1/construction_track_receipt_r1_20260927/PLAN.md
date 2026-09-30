# Issue #2476 — track-receipt boundary construction rung

Allocation: `issue2476-track-receipt-construction-r1-20260927`
Parent hypothesis: [#2476](https://github.com/Unjuno/agent-interface/issues/2476)
Predecessor: #729 `HOLD_MATCHER_RANGE`; its ten formal cases remain untouched.

## H / T / D / C / U

### H — hypothesis

A typed, short-lived track receipt can represent a *current visual-observation
candidate* only while its accepted-match anchor, signed correction direction,
bounded predicted displacement, frame sequence, geometry, timestamp, score and
uniqueness margin all satisfy frozen limits. The receipt alone must never admit
an input candidate. A separately bound, unexpired, one-frame authority lease is
also required. Abrupt translation, target loss, ambiguity, stale evidence,
geometry changes and malformed direction must fail closed even if a global
fallback match claims a high score.

### T — smallest falsifiable rung

One deterministic, synthetic construction block of 15 rows in a local
`linux/amd64` Docker container, with no GUI, game, OS input, model/provider,
network, randomization, retries or tuning. Inputs are explicit in `cases.json`.
The construction exercises a valid in-corridor observation, receipt without
authority, current-vs-stale/mismatched authority, exact inclusive score/margin/
corridor/age boundaries, below-threshold and ambiguous matches, stale age,
frame gaps, geometry change, missing target, abrupt translation with an
apparently strong full-frame fallback, direction mismatch, expired lease, and
future-dated observation. Runner and auditor execute as separate Docker
processes against read-only source. The auditor independently recomputes every
row from the frozen input and raw trace.

### D — decision gates

`PASS_TRACK_RECEIPT_BOUNDARY_CONSTRUCTION_ONLY` requires source/input hashes to
match; all 15 rows to reconcile under the independently reimplemented gates;
only the valid and exact-boundary cases to admit an action *candidate*; the
receipt-only case to have no candidate; every invalidation control (including
the strong global fallback on abrupt translation) to abstain; and zero physical
input emissions. Any mismatch is `FAIL_CONSTRUCTION_GATE` and the retained
trace is not repaired or rerun.

This is not the #2476 formal allocation. In particular it does not implement
pixel matching or BASELINE-vs-TRACKED arms and cannot establish a trajectory,
task effect, safe live input, target identity, or improvement. It only falsifies
the typed receipt / independent-authority boundary before any live study.

### C — controls

The experiment executes only the predeclared synthetic cases. The simulated
authority object is test input, not a runtime permission or OS-input channel.
No thresholds, case order, source or image may change after freeze. No
predecessor #729 seed, frame, session or output is read by the runner.

### U — limits

No VizDoom frame, visual matcher, temporal trajectory, X11 release, physical
key state, semantic target relation, production controller, user task, model,
latency benefit or product capability is tested. A construction PASS is not a
formal #2476 result and authorizes no integration or promotion.

## Frozen rules

- The previously accepted anchor itself must have score `>= 0.80` and margin
  `>= 0.08`.
- A current observation must be `FOUND`, score `>= 0.80`, margin `>= 0.08`, and
  bind a nonempty frame SHA-256.
- Geometry is exactly `640x480` and must equal the anchor geometry.
- Frame sequence advances by 1 or 2; capture age is in `[0, 250000000]` ns.
- The receipt's signed `(dx, dy)` must match `LEFT/RIGHT/UP/DOWN`, have each
  component within 8 px, and predict the observed center within 8 px on each
  axis. Bounds are inclusive.
- A corridor miss cannot be silently re-anchored by a high-scoring full-frame
  fallback; it abstains.
- An action candidate requires a separate `corrective_input` lease whose frame
  sequence and digest exactly match the current observation and whose validity
  interval contains the capture timestamp. No physical input is emitted.

