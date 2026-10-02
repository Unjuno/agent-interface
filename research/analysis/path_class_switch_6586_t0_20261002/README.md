# Path-class switching T0 — finite embedded-route method check

Status: **successor construction complete (14/14); formal candidate/auditor not run**.

The earlier abstract-token attempt is separately retained in draft PR [#6596](https://github.com/Unjuno/agent-interface/pull/6596) as `FAIL_OR_HOLD` after its independent replay audit failed and the Issue's planar-embedding controls were found missing. This successor has a new allocation ID and tests the corrected source-visible embedded geometry contract. It preserves the predecessor unchanged.

This additive package tests Issue #6586's finite T0 method contract. It does not rerun or edit #630/#2988 and is not a DOOM/game result.

## H / T / D / C / U

**H.** In the frozen planar route fixture, a source-visible common blockage on one obstacle-side class lets a class-aware selector reach the subgoal with fewer repeated same-class route attempts under a fixed event budget than either novelty-only exploration or simple backtracking. The controls must refuse a unique class at a shared prefix, refuse a same-class apparent branch, invalidate stale geometry, reject an unsupported class cue, and yield when only one class exists.

**T.** One standard-library-only WSLc construction suite, then one candidate invocation and one separate raw-only auditor invocation. Six frozen cases × three policies = 18 candidate rows. The positive family has three upper-side variants sharing one visible gate and one lower-side alternative; the controls cover shared-prefix ambiguity, two upper routes in the same class, geometry revision, false cue, and a single-class map. Candidate input and independent oracle are separate files. The candidate receives only `inputs.json`; the auditor receives the additional `oracle.json`.

**D.** `PASS_METHOD_SCOPED` only if the auditor reconstructs all 18 rows; in the positive control the class-aware arm selects the unblocked LOWER path, reaches the subgoal at cost 6/6 with zero same-class reentries, and both fixed baselines exhaust the same budget after two upper-route reentries; all five controls retain their frozen refusals; every geometry/class label is independently recomputed; and audit errors are zero. Any raw/identity/geometry disagreement is STOP/FAIL without retry. A clean but absent planted gain is `HOLD_NO_METHOD_ADVANTAGE`.

**C.** The obstacle is the rectangle `[-0.5, -1, 0.5, 1]`; completed route classes are independently assigned by the sign of the path's intersection with x=0 outside the obstacle. The positive case's route-attempt costs are authored finite units, not seconds, pixels, or learned costs. Novelty-only and backtracking are deterministic stylized baselines fixed in `candidate.py`; no outcome is generalized beyond this deck.

**U.** No real map discovery, perception, dynamic environment, game/GUI control, model, human, physical input, release behavior, latency, navigation benefit, safety guarantee, or product result. An independent geometry oracle over authored paths does not validate a visual agent's ability to infer the map or topology.

## Frozen controls and expected behavior

- `blocked_class_positive`: upper-side variants are blocked at one visible gate; the lower route is open. The shared current prefix is ambiguous, but the retained source-visible prior-attempt prefix supports UPPER. Class-aware grouping is allowed only because every candidate route in that observed class intersects the same visible barrier.
- `shared_prefix_ambiguous`: the prefix remains compatible with UPPER and LOWER; class-aware output is `UNKNOWN_CLASS` with no route.
- `same_class_deceptive_branch`: both apparent alternatives classify UPPER; output is `NO_DISTINCT_CLASS_SWITCH`.
- `geometry_revision`: observed and current map versions differ; output is `REOBSERVE` after embedding invalidation.
- `false_class_cue`: the alleged upper blockage intersects no visible barrier; output is `UNKNOWN_CLASS`.
- `single_class_graph`: no supported alternative class exists; output is `SAFE_YIELD`.

The upper alternatives share a previously visited prefix, so each repeated same-class route trial increments the frozen `revisits` measure. This is a count of repeated route-prefix attempts in the synthetic fixture, not a real-world movement or time measure.
