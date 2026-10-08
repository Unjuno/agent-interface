# Rendered X11 deadband transfer v1

Status: **PASS for rendered Xvfb/XTest stop mechanics; no MAP01/model efficacy claim.**

This experiment transfers the deadband candidate from the synthetic adversarial sweep into an actual rendered X11 fixture. A Tk task renders a red marker. The controller reads only root-window pixels through X11 and actuates with XTest Left/Right key events. Exact task state and app-observed input transitions are written separately and read after the arm finishes.

Six arms ran in alternating baseline/deadband order: three with no target deadband and three with `abs(x) < 0.06` as a local stop condition. Every arm starts from the same rendered source position near `x=0.20` and admits the same Left key action.

Results:

- baseline 3/3 continued until the directional guard reached the center crossing (`direction` cancel);
- deadband 3/3 cancelled naturally on the target deadband before the center crossing;
- baseline median app-observed release state: `x=0.0045`;
- deadband median app-observed release state: `x=0.0505`;
- all 6 arms had exactly one app-observed KeyPress and one KeyRelease;
- all 6 terminal key states were empty;
- maximum controller release-send to app-observed KeyRelease was **0.478617 ms** in this container fixture.

The deadband does not prove a better task outcome here; this fixture is intentionally only a stop/release transfer. It establishes that a task-relative local termination condition can be evaluated from rendered pixels and cause actual XTest release before the weaker direction-only guard would stop.

The executed script SHA-256 is `d4ada3bc7346e7426882959fb57558dfd884cd2ae99cc9885cd5cfbf7f4cd4ee`; the full first result JSON SHA-256 is `576006b5390d9d03a1176c735dae122f395f758bfc5f0f9fec77a0e6f663e9ab`.

## H / T / D / C / U

**H.** A task-relative target deadband can stop a still-fresh prior action before the weaker direction/source guard reaches its own invalidation boundary, while preserving balanced physical input and terminal empty release.

**T.** Three baseline and three deadband rendered Xvfb/XTest arms, requiring natural deadband cancellation in every candidate arm, one press/one release per arm, and terminal empty input.

**D.** **PASS rendered mechanics.** Deadband cancellation occurred 3/3; balance and terminal empty release passed 6/6. This does not promote a MAP01 deadband value.

**C.** The one-dimensional rendered task is much simpler than gameplay semantics; its target region is development-authored and obvious; Xvfb scheduling differs from WSLg and real desktops.

**U.** Domain-specific postcondition authorship, delayed visual effect, noisy target semantics, and interaction with the formal recovery lease remain untested.

## Next gate

Do not tune `0.06` against MAP01 outcomes. The next domain transfer must define a preregistered task-relative continuation/termination predicate from MAP01-observable evidence, then test it under a new versioned formal allocation. The current formal recovery allocation remains untouched by this branch.
