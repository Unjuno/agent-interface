# T0S4 formal auditor STOP

Disposition: `STOP_AUDITOR_SCHEMA_ASSUMPTION / NOT_EVALUATED`.

The frozen candidate ran once in the registered OrbStack container and exited 0. It produced 80 rows in `results/formal-01/raw.json`, SHA-256 `81e8e0f9d34de42272744a3793162fe0cb857c77b8e67f28108f28dfc4bc8e49`.

The one allocated auditor process ran once and exited 1 before reconstruction completed. Exact first exception: `KeyError: 'envelope_violations'` at `audit.py:67`, because the frozen audit assumed refusal rows contain schedule metrics. Refusal outputs intentionally contain only refusal status, empty moves/positions, release, and switch count. This is an auditor defect; it is not evidence that the candidate passed or failed the method hypothesis. `audit.json` was not created.

No retry, patched replay, or candidate re-execution occurred. The immutable raw is consumed only by a distinct audit-only successor with its own ID, path, source freeze and one-shot budget.

Exact formal commands:

```text
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --pids-limit 32 --cpus 0.5 --memory 128m -v <package>:/src:ro -v <formal-output>:/out:rw -w /src python:3.12-alpine python -B candidate.py fixture.json /out/raw.json
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --pids-limit 32 --cpus 0.5 --memory 128m -v <package>:/src:ro -v <formal-output>:/out:rw -w /src python:3.12-alpine python -B audit.py fixture.json /out/raw.json /out/audit.json
```

Candidate exit 0; auditor exit 1. The captured exception above is the auditor stderr excerpt. Image ID, source hashes and preregistration are in `FREEZE.json` and the linked Issue comment.
