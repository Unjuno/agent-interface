# Scope correction — Issue #5550 T0

This additive clarification supersedes the final two sentences of `PLAN.md`'s **U** bullet, which incorrectly said that the supervisor table was hand-specified and not inferred by a synthesis algorithm. The formal raw, audit output, preregistered source freeze, and `REPORT.md` result are unchanged; no experiment or audit was rerun for this correction.

The candidate in the frozen `model.py` computes a fixed point over the declared plant: it iterates uncontrollable safety closure and backward coaccessibility, then enables every controllable transition internal to the resulting winning region. The independent frozen `audit.py` uses a different method: it enumerates all 64 subsets of six controllable edges, retains policies whose reachable states remain safe and nonblocking, and unions their enabled edges. On the retained raw, the independent enumeration found 44 valid policies and matched the candidate's maximal enabled-edge set.

Corrected uncertainty boundary:

- The result supports fixed-point supervisor synthesis and edge-set maximality **for this exact hand-authored, finite, fully observed DFA and its declared marking/safety rules**.
- It does not validate a general-purpose synthesis implementation, completeness of the state/event abstraction, uncontrollable-event classification in a real interface, partial observation, asynchronous timing, GUI effects, or runtime integration.
- The recovery transitions (`REACQUIRE`) are part of the hand-authored plant. The measured completion difference is consequently a property of this fixture, not evidence that a live interface will recover or make progress.

The competing explanation in `PLAN.md` remains: conservative fail-closed may be preferable when real observation is partial or when the modeled recovery transitions are unavailable. The unresolved question is transfer from this finite model to an adequately observed real interface, not whether a policy was computed in this finite experiment.
