# Threshold-persistent topology T0 for Issue #6183

This package tests a synthetic **visual connectivity predicate only**. It is
not an app-effect, GUI, route-graph, or user-benefit experiment. App effect is
`UNKNOWN` for every row. See `PREREGISTRATION.md` for the frozen H/T/D/C/U and
decision gate, `candidate.py` for the image-only method, and `audit.py` for an
independent replay.

## Artifacts

- `fixtures.json`: image-only input; no expected or hidden-graph labels.
- `labels.json`: separate authored visual truth and hidden-graph controls;
  auditor-only input.
- `candidate.raw.json`: exact candidate output, copied from the dedicated VM.
- `audit.json`: independent replay, metrics, and gate check.
- `RUN.json`: identities, exact commands, exit statuses, environment limits,
  and output hashes.
- `SHA256SUMS`: hashes for frozen source and retained outputs.

## Reproduction

The formal candidate and auditor each run once in separate containers on the
private Docker Engine inside OrbStack VM `research-6183-t0-20261003`. The image
is pinned by digest in `RUN.json`; network is disabled at container runtime.
The source mount is read-only and output mount is separate and writable. The
VM is configured for 1 vCPU/2 GiB; each container is configured for 1 CPU/512
MiB. `RUN.json` records the cgroup values actually observed in the container.

No GUI, game, model, live application, external route graph, or user data was
used. A method-scoped synthetic pass cannot close Issue #6183 or establish
application semantics.
