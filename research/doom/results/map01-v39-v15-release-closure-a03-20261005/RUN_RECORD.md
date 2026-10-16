# A03 run record

- Run ID: `MAP01-V39-V15-RELEASE-CLOSURE-A03-20261005`.
- Exact source: `origin/main` `6f34c5c0c5bc3116d8e7c25f29aa1b92cc4a01b1`; 40 source blobs locked in `FROZEN_INPUTS.json` and copied under `src/`.
- Image: `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (cached image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`).
- Candidate: one no-network WSLc container, 1 CPU, configured 512 MiB, readonly `/src`, writable `/out`; candidate exit 0. Exact stdout, container inspect and exit code are retained.
- Independent raw auditor: one separate no-network WSLc container with the same resource/mount configuration; exit 0, `PASS_AUDIT`, zero errors.
- Candidate result: exact V15 backend `doom_owner_thread_release_batch_backend_v1.Backend` and Executor `executor_v13.Executor`; two admissions (F8, SPACE), two reverse releases (SPACE, F8), identity joins pass; final owner/backend state empty, release verified, authority false, owner stopped.
- Raw release interval operation trace: no `query_keymap` between the two key-up injections (0 inter-release queries). A later final batch reconciliation query occurs after both releases. Disposition: `NO_INTER_RELEASE_QUERY_OBSERVED`.
- WSLc emitted: “Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.” Configured memory is not claimed as an enforced hard limit.
- No game/session startup, real X server, OS input, model, task effect, recovery, live allocation, latency bound, safety, or MAP01 progress was tested.
- Pre-run: `python -B audit_import_closure.py` previously passed for 38 production Python modules; A03 pre-run static syntax/source-lock/output-absence gate also passed. A01 and A02 packaging STOPs remain separately retained and unmodified.

The candidate command used:

```powershell
wslc run --pull never --network none --cpus 1 --memory 512m --mount "type=bind,source=<package>\src,target=/src,readonly" --mount "type=bind,source=<package>\out,target=/out" --name map01-v39-v15-release-a03-20261005-candidate python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B /src/candidate.py
```

The independent auditor used a distinct container name ending `-auditor` and ran `python -B /src/audit.py` after candidate exit 0.
