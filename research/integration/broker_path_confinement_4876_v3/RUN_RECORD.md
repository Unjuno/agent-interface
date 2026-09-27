# Run record — #4876 allocation 03

Local Windows PowerShell invoked Docker Desktop Linux/amd64. Formal command (host paths abbreviated to the checked-out workspace root):

```powershell
docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,noexec,size=16777216 --cap-drop ALL --security-opt no-new-privileges --pids-limit 32 --memory 256m --cpus 1 --mount "type=bind,source=<workspace>\research\integration\broker_path_confinement_4876_v3,target=/src,readonly" --mount "type=bind,source=<fresh outputs\broker-path-confinement-4876-formal03>,target=/out" --workdir /src --entrypoint python python:3.13-slim@sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0 -B /src/runner.py /out/formal
```

Runner exit: 0. It emitted one raw file; no external CLI was invoked. Raw output is retained in `RAW.json`.

The independent audit ran once in a second Docker container with source and raw mounted read-only, network disabled, and separate writable output. It emitted `PASS_INDEPENDENT_AUDIT`; the same audit invocation ran six mutations on deep-copied JSON values only and rejected 6/6.

A post-run read-only Docker integrity check compared all `FREEZE.json` source hashes and compiled source strings in memory (no pyc writes): `freeze_all_match=true`, `compile=PASS`.


