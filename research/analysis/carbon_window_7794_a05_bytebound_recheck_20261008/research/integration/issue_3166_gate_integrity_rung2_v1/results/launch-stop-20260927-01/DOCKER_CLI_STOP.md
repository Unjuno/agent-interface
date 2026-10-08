# Pre-formal Docker CLI STOP — 2026-09-27

- Allocation: `issue3166-gate-integrity-rung2-20260927-01`
- Stage: host-side Docker CLI argument validation, before container creation
- Exit: 125
- Container name requested: `issue3166-rung2-formal-20260927-01`
- `docker inspect`: `error: no such object: issue3166-rung2-formal-20260927-01`
- Evidence mount at stop: empty; no `raw.jsonl`, source hashes, or result rows
- Classification: `STOP_DOCKER_LAUNCH_ARGUMENT`, not a scientific outcome

Captured stderr:

```text
invalid argument "type=bind,source=/tmp/issue3166-gate-integrity-rung2-20260927-01,target=/evidence,rw" for "--mount" flag: invalid field 'rw' must be a key=value pair

Usage:  docker run [OPTIONS] IMAGE [COMMAND] [ARG...]

Run 'docker run --help' for more information
```

No container started. The corrected mount spelling is recorded separately in
`../LAUNCH_ERRATUM.md`; no experimental condition or frozen source was changed.
