# Formal allocation 01 — 2026-10-03

## Disposition

**PASS_METHOD_SCOPED.** The finite synthetic ledger separately reconstructs event-count and union-duration opportunity coverage. This does not validate a live controller, establish task value, or support a human-tempo or product claim.

## Invocation accounting

- Construction checks: WSLc container, 7/7 unittest checks passed.
- Candidate formal invocation: 1, exit 0; schema `exogenous-opportunity-event-time-a02-v1`; three scenarios.
- Independent auditor formal invocation: 1, exit 0; `PASS_METHOD_SCOPED`; zero errors; six routes and three scenarios reconstructed.
- Scientific retries: 0. One auditor container start was refused before container creation due to an incorrect UNC mount source; no auditor process ran then. Corrected path was used for the single successful auditor invocation.
- Earlier source mount preflight against Windows-backed workspace failed (`E_INVALIDARG`, Access is denied); no candidate/auditor process ran. A large shallow clone was started while diagnosing but did not complete; it was interrupted. No repository source or unrelated WSL container was changed.
- Frozen-source preregistration hash was corrected before formal run: GitHub MCP blob bytes and decoded GitHub API blob both yield SHA-256 `0f3e2ba44c84b2cd02d3001fbb050c34ce0589c45402db5924d63e2dc6aa6721`. The initial recorded `7b73...` did not match the content; no executable source was changed.

## Runtime

- Engine: Microsoft WSL Containers / `wslc.exe` 3.0.1.0.
- Image: `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, local image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`, linux/amd64, Python 3.12.15.
- Requested: pull never, network none, CPU 1, memory 256m, uid/gid 65532, source read-only; auditor candidate-evidence mount read-only; distinct writable output mounts.
- WSLc warning on invocations: kernel lacks swap-limit capability / cgroup is not mounted; requested memory cap was not demonstrated as fully enforced.
- No GPU, package installation, model, GUI, application, network access from within formal containers, or runtime import.

## Results against gate

- Equal durations: event 2/4 and time 20/40.
- Heterogeneous durations: long-only event 1/11, time 90/100; shorts-only event 10/11, time 10/100. The estimands rank these routes oppositely.
- No onset schedule: both denominators null; `HOLD_NO_ELIGIBLE_ONSET_CLOCK`.
- Mutation controls rejected: omitted short opportunity, altered duration, double-counted interval claim, and fabricated missing onset schedule.
- Candidate raw output SHA-256: `9193c79c61564bfe1a5c633761ef9dee49d7a348bb08b0bfbf98a44fff965f20`.
- Audit raw output SHA-256: `e3785d28ff421f01f8d39efdd5fc29f2cc5874a5e5428fab94bbf38c9f36ce5c`.

## Scope and handoff

Use both reported denominators only when the task question explicitly distinguishes event opportunity from eligible wall-clock occupancy and their source clocks/eligibility are declared. Duration is not severity or task value. No-onset tasks must not be assigned synthetic opportunity denominators. Overlapping cue attribution, policy-dependent opportunity generation, live route comparisons, effect quality, safety and user benefit remain untested.
