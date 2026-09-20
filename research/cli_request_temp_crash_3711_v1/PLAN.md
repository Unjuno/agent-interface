# Issue #3752 — request-temp crash probe

Allocation: `issue3752-request-temp-crash-01`.

Parent: [Issue #3711](https://github.com/Unjuno/agent-interface/issues/3711). Successor: [Issue #3752](https://github.com/Unjuno/agent-interface/issues/3752).

Base: `main` at `76965311d899815174b5ed081ff439bd4533ef63`. Frozen target `runtime/cli_v1/attempt.py` Git blob SHA-1: `70cc62b450c8b9c8aaa0db49b1e116388368fe4c`. The one-shot runner `experiment.py` is bound by Git blob SHA-1 `02c05b5fad754c08fa7e77d268bd593826dd487b` and branch commit `ec6dd79ebb2ed0d397cd18cd2a6decc30f5f7757`. Do not modify either frozen input; any change requires a new allocation.

## H/T/D/C/U

- **H — Hypothesis:** An abrupt process exit during a partial write to `.request.json.tmp`, before the request is atomically published or the backend is invoked, leaves an unknown attempt. Public `attempt-status` reports `unknown_or_incomplete`, `replay_allowed=false`, and lists the residue without mutation. Reusing the directory refuses before backend and preserves the complete snapshot.
- **T — Test:** The single runner starts a child process whose patched file writer writes and flushes half of the exact expected request JSON, then calls `os._exit(29)`. Parent assertions: expected child exit, absent request/report/backend marker, strict-prefix temp bytes, two real CLI `attempt-status` subprocesses with exact non-replay state, unchanged recursive directory snapshot after each inspection, and same-directory `invoke` refusal before a mocked backend. No GUI/model/input/network.
- **D — Decision:** PASS only if all assertions hold; contradiction is FAIL. Any frozen-source mismatch, non-empty output directory, unavailable image/engine, or harness launch problem is STOP before a scientific conclusion. One run only. The result file records disposition, hashes, exact status output and snapshots.
- **C — Constraints:** Local Docker/OrbStack, `linux/amd64`, Python 3.12 image pinned by digest, `--network none`, read-only source/root, bounded writable output and tmpfs, one CPU and 512 MiB limit. The current attached PC is STOP before allocation (C: 0 free bytes; Docker engine unavailable); no run is claimed.
- **U — Scope:** One process-level crash boundary during request-temp publication. Not power-loss durability, arbitrary filesystem semantics, stale-temp cleanup safety, native effects, or full #3711 adoption. Prior #3725/#3735 evidence remains immutable.

## Command (only after local capacity and Docker preflight pass)

Run from a checkout of this exact branch. Allocate a unique, empty host output directory outside the checkout:

```sh
output="$(mktemp -d "${TMPDIR:-/tmp}/issue3752-request-temp-crash-01.XXXXXX")"
test -z "$(find "$output" -mindepth 1 -print -quit)"
docker run --rm --platform linux/amd64 --network none --read-only \
  --tmpfs /tmp:rw,exec,size=64m --pids-limit 32 --memory 512m --cpus 1 \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,source="$PWD",target=/src,readonly \
  --mount type=bind,source="$output",target=/out \
  --env SOURCE_ROOT=/src \
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python /src/research/cli_request_temp_crash_3711_v1/experiment.py /out
```

The output must be archived under a fresh, allocation-specific evidence path only after the one-shot run and independent review. Never mount a committed result directory as `/out`.

## Independent audit command

Auditor: `audit.py`, Git blob SHA-1 `46915fdf2d095af2c737f0761241bc67400b36f1`. Run in a **second fresh container** only after the runner has completed and its output is preserved. The output mount must be writable for `audit.json`; all formal evidence inputs are read-only from the auditor's perspective.

```sh
docker run --rm --platform linux/amd64 --network none --read-only \
  --tmpfs /tmp:rw,exec,size=64m --pids-limit 16 --memory 256m --cpus 1 \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,source="$PWD",target=/src,readonly \
  --mount type=bind,source="$output",target=/out \
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python /src/research/cli_request_temp_crash_3711_v1/audit.py /out /src
```

The current result remains `STOP_LOCAL_CAPACITY_BEFORE_ALLOCATION`; neither command has been run.
