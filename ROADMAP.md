# Roadmap

This roadmap is ordered by research uncertainty, not by feature count.

## Now — Observation Gating

Goal: remove visual/model input that carries no new task-relevant information while keeping correctness as a hard gate.

- [ ] Freeze O0: full screenshot after each logical step.
- [ ] Add O1: exact unchanged-frame suppression.
- [ ] Add O2: exact changed-tile / spatial-delta feedback.
- [ ] Add O3: relevant-region gating.
- [ ] Add O4: local `VERIFY` before model escalation.
- [ ] Measure action-to-first-useful-feedback latency.
- [ ] Measure image-observation elimination at equal correctness.
- [ ] Stress tiny but semantically important changes so approximate hashes cannot silently hide them.

Active track: [`research/observation_gating/`](research/observation_gating/).

## Next — automatic speculation and guard policy

- [ ] Estimate guard cost vs `P(stale) × failure cost` per route.
- [ ] Automatically select pre-execution guard vs postcondition-only verification.
- [ ] Continue separating binding, precondition, route, observation-cache, and motor-calibration lifetimes.
- [ ] Run longer multi-app sessions with focus drift, window replacement, modal transitions, and geometry changes.

## Runtime consolidation

Goal: turn promoted research semantics into one coherent component without freezing the architecture too early.

- [ ] Consolidate promoted primitives under `runtime/`.
- [ ] Provide a model/vendor-neutral local boundary.
- [ ] Add a thin CLI for setup, inspection, and demos.
- [ ] Keep deterministic fast loops local; do not fork a CLI process per action.
- [ ] Expose immediate/incremental feedback so the agent is not blocked on unnecessary waits.
- [ ] Preserve Universal Control as the fallback floor.

## User-facing runtime preview

A GitHub Release is cut only when a user can actually download and try it.

Required before the first runtime preview:

- [ ] runnable package or executable archive;
- [ ] checksum;
- [ ] minimal quickstart;
- [ ] supported OS/backend statement;
- [ ] smoke test / self-check;
- [ ] correctness gate across multiple real apps;
- [ ] recovery semantics and observation gating integrated;
- [ ] link from the release to the research evidence supporting the promoted behavior.

See [`release/README.md`](release/README.md).

## Later — production stabilization

- [ ] Freeze executable IR and error taxonomy.
- [ ] Port the frozen hot path to a systems implementation.
- [ ] Native backends beyond X11.
- [ ] Actual model-in-loop measurements: model calls, text tokens, image tokens, end-to-end latency.
- [ ] Broader app/toolkit suite and external reproduction.

## Stable release gate

A stable release requires substantially frozen protocol/execution semantics, explicit recovery behavior, cross-platform evidence, and a support envelope that is narrower than the evidence rather than broader than it.
