# Issue #6691 T0 allocation 01 — STOP

Disposition: `STOP_AUDITOR_CONTAINER_LAUNCH`; no method PASS/FAIL disposition is accepted.

The frozen candidate completed once in OrbStack and emitted `37` rows in each of two authored cases. The independent auditor did not start: the Docker bind-mount source path in the sole auditor command was mistyped (`version-defined-intervention-6691-t0-20261002` omitted `-orbstack-`). OrbStack returned `invalid mount config ... bind source path does not exist`, exit `125`, before Python/auditor code ran. This is an orchestration error attributable to this run, not a scientific result.

The preregistered allocation allowed one candidate and one auditor invocation with no retry or repair. Candidate count is 1; auditor launch-attempt count is 1, completed auditor evaluations 0. No corrected command, host audit, or rerun was performed. Candidate JSON/stdout/raw rows are retained unchanged, but candidate summaries are unverified descriptive output only and do not satisfy the independent-audit gate.

## Frozen provenance and runtime

- Issue: [#6691](https://github.com/Unjuno/agent-interface/issues/6691)
- Source commit: `ab3650b8a09bcb6b8878a71c185ba48f980ba4d2`; refreshed main base: `c8e8bccd6dd96fda518111b526bd499582186566`.
- Source/image identities and H/T/D/C/U: [FREEZE.md](FREEZE.md), [PLAN.md](PLAN.md).
- Candidate container: `python:3.12-slim-bookworm` at image ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, Python 3.12.14, linux/arm64. OrbStack Engine 29.4.0, cgroup v2.
- No network, read-only root, dropped capabilities, no-new-privileges, uid/gid 65534; requested 0.25 CPU, 256 MiB memory and 32 pids. A separate runtime preflight observed `cpu.max=25000 100000`, `memory.max=268435456`, `pids.max=32`, and `memory.swap.max=268435456`. These are observed cgroup values for the preflight container, not a performance result or proof about the failed auditor container.
- Candidate stdout, exit marker, JSON and raw rows are retained. Auditor stdout and exit marker preserve the exact launch error.

## Exact launch record

The candidate used read-only `/src` from the frozen experiment directory and writable `/out` from this allocation directory; exit 0. The single auditor launch used a misspelled source directory in its `/src` bind mount, so Docker rejected it before container creation; exit 125. See `candidate.stdout.log`, `candidate.exit.txt`, `auditor.stdout.log`, and `auditor.exit.txt`.

The consumed allocation remains STOP. Any future study must be a separately authorized, genuinely distinct successor allocation; this record is not an invitation to repeat or repair the same formal run.
