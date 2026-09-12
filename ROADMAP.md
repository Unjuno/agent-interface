# Roadmap

This roadmap is ordered by research uncertainty, not by feature count.

## Now — observation without wasted model input

- [ ] Establish O0 full-observation baseline on real-app sessions.
- [ ] Add exact/fast unchanged-frame suppression.
- [ ] Compare global hash, perceptual hash, tile signatures, and multi-resolution change vectors.
- [ ] Gate irrelevant changed regions before model-visible observation.
- [ ] Add local `VERIFY` for simple state-change predicates.
- [ ] Measure image-observation elimination at equal correctness.
- [ ] Quantify false-negative / false-positive gating cost.

## Next — automatic speculation policy

- [ ] Estimate `guard cost` vs `P(stale) × failure cost` per route.
- [ ] Automatically select pre-execution guard vs postcondition-only verification.
- [ ] Separate binding, precondition, route, observation-cache, and motor-calibration lifetimes.
- [ ] Longer multi-app sessions with focus drift, window replacement, modal transitions, and geometry changes.

## Runtime consolidation

- [ ] Consolidate the research primitives behind one Python experimental runtime surface.
- [ ] Version the research protocol only when semantics are stable enough to compare across releases.
- [ ] Add a persistent process/IPC demo only after it reflects the promoted algorithm, not an obsolete prototype.

## Later — production stabilization

- [ ] Freeze the executable IR and error taxonomy.
- [ ] Port the frozen hot path to a systems implementation.
- [ ] Native backends beyond X11.
- [ ] Model-in-loop measurements: actual model calls, text tokens, image tokens, end-to-end latency.
- [ ] Broader app/toolkit suite and external reproduction.

## Release gates

### Research preview

- reproducible harnesses and raw summary CSVs;
- explicit environment/limitations;
- no unsupported production claims.

### Runtime preview

- coherent runnable interface;
- correctness hard gate across multiple real apps;
- recovery semantics and observation gating integrated.

### Stable

- protocol and execution semantics substantially frozen;
- cross-platform evidence;
- independent/external reproduction desired before strong performance claims.
