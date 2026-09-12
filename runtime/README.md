# Runtime

This directory is reserved for the user-facing Agent Interface runtime.

The project is still research-first, so experimental benchmark code remains under `research/`. Code moves here only when it represents the current promoted semantics rather than a one-off experiment.

## Target properties

A runtime preview should be:

- quick to install or unpack;
- agent- and model-agnostic;
- usable on unknown applications through universal control;
- responsive enough that the agent is not blocked waiting for avoidable interface latency;
- local-first for deterministic control, feedback, verification, and recovery;
- explicit about uncertainty and able to fall back safely.

See `../docs/principles.md` for the design constraints.

## Planned surface

The eventual runtime is expected to expose a small local library/protocol surface plus a thin CLI for setup, inspection, and demos. High-frequency control should not require spawning a new process or crossing a remote boundary for each action.
