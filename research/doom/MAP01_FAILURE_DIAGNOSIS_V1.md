# Retained MAP01 failure diagnosis and one-way visual invalidation

The retained Astra MAP01 run exposes two distinct control failures. Fixed cover
ended before seven model returns, producing 9.771 seconds of uncovered inference
tails and a 3.765-second maximum. More importantly, expiry is not the whole
failure: the exact decision frames show health falling
`100,100,100,100,100,84,84,53,49,22,11,4,0`. Eighty-four health points were
lost across decision-to-decision windows whose inference cover was `coast`.
Each window also includes the following primary program, so this association
does not attribute the damage to cover alone.

The run saw visible enemies at decision 3 and used an active strafe/fire cover
in the following inference interval. Later assessments recognized damage and
falling health without a currently visible enemy, while fixed inference cover
returned to coast. The current v23 responder still requires a visible threat
for a nonempty `next_cover`. Renewal fixes time coverage, but repeating a coast
policy does not react to new evidence that the policy has become inappropriate.

## Revisited candidate

The earlier single-ROI changed-pixel barrier was rejected because it treated
generic visual change as evidence that a task-relative postcondition succeeded.
An Inkscape drag moved only half the requested distance, yet the barrier allowed
the next Save. That remains a valid rejection for continuation authority.

The same weak signal has a safer asymmetric use: it may invalidate an already
admitted policy, but it may never establish success or grant new input. The new
`policy_invalidation_guard_v1.py` therefore has only three outcomes:

- `UNCHANGED` leaves the existing policy unchanged;
- `INVALIDATED` requires a new decision;
- `UNKNOWN` also requires a new decision.

Changed binding, frame geometry, nonadvancing sequence, invalid time and expiry
all return `UNKNOWN`. The outcome explicitly says it grants no input authority
and can only reduce existing authority.

On the 12 adjacent pairs of exact retained decision frames, a tight health-digit
ROI with RGB threshold 32 and minimum 100 changed pixels separates all seven
health changes from all five unchanged pairs. A nearby animated face ROI
invalidates on 12/12 pairs, demonstrating that region choice matters. This is a
posthoc calibration, not a live reliability estimate. The generated HUD contact
sheet makes the manual health/ammo/armor transcription reviewable against the
hash-checked frames.

Run the pure boundaries and retained analysis with:

```sh
PYTHONPATH=research/live_control python research/doom/test_policy_invalidation_guard_v1.py
PYTHONPATH=research/live_control python research/doom/analyze_map01_astra_failure_v1.py
```

The next live allocation should keep v23/schema v3 and add exact HUD-region
observations during cover. Region change may cancel the repeated policy and
escalate, or switch only to a separately bounded and admitted conservative
policy. It must not claim to understand whether the value rose or fell. Retain
the first threat-exposure result, including no exposure, death, or failure.

The first newly frozen v23 allocation (`map01-cover-threat-v23-live-01`) is
retained as a pre-GUI environment failure. Its command used `/usr/bin/python3`
without the repository `_vizdoom` target on `PYTHONPATH`, so the child session
could not import ViZDoom. No model call, GUI-ready event, or input admission
occurred. A command-free import diagnostic confirms that the default interpreter
cannot see ViZDoom and that `PYTHONPATH=_vizdoom` exposes the retained 1.3.0
package. Any corrected execution must use a new allocation ID and output path.
