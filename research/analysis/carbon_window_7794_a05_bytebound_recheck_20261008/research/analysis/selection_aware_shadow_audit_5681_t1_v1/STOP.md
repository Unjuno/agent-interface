# Allocation #03 STOP — candidate command divergence

## Disposition

`STOP_CANDIDATE_COMMAND_DIVERGENCE`. The one-shot candidate invocation was consumed (candidate=1); the independent auditor was not run (auditor=0). This is an execution/provenance STOP, not a scientific FAIL and not `METHOD_PASS_SCOPED`. Do not retry this allocation.

## Frozen inputs

- Repository: `Unjuno/agent-interface`
- Main observed at start: `2669f307ee2176df963fad3409193da465ffe546`
- Branch: `research/selection-aware-shadow-audit-5681-t1-20261001`
- Branch HEAD: `80746781ca5670cf70c04e1feba3af3d25938a80`
- Candidate SHA-256: `82a1f19d46427ceab3bb08b35dba9af94ab4a67d581d8fa184cc6f2d416a20de`
- Auditor SHA-256: `5b43c5dfdb6c61bd080ac8728cf8a9966f8ae373449057c0745cf0e82f50a694`
- PLAN SHA-256 before this STOP note: `97a021c84799b6b39fa05f98e7f342a1ed0ef6d5be85893ed6412c460c1db45d`
- Test SHA-256: `26cc0fd4d8ee39426b3f599b546827f67f2fb98508ff26a905a718e4c61ccb25`
- Isolated guest Docker: 29.8.2; `docker-ce` and `docker-ce-cli` `5:29.8.2-1~ubuntu.24.04~noble`; `containerd.io` `2.3.6-1~ubuntu.24.04~noble`; overlayfs; cgroup v2; aarch64.
- Image: `python@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, `linux/arm64`.
- Transferred source hashes in guest matched the frozen local candidate/auditor hashes above.

## Invocation and fault

The sole candidate container command was:

```text
orb -m obs-audit-t1-5681-20261001 sudo docker run --platform linux/arm64 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m --cpus=1 --memory=512m --pids-limit=64 --mount type=bind,src=/home/taka/t1-src/candidate.py,dst=/candidate.py,readonly --mount type=bind,src=/home/taka/t1-out,dst=/out --entrypoint python python@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e -c 'import runpy; print(runpy.run_path("/candidate.py")["build"]())'
```

This diverged from the planned `python /candidate.py` CLI invocation and did not redirect stdout to `/out/candidate.json`. The tool returned a large Python dict representation rather than JSON. That rendered output was truncated by the command-result limit and no byte-exact raw output or explicit exit code was retained. Consequently there is no auditable candidate artifact and no valid input for the independent auditor. The stopped machine's transient container was launched with `--rm`; no container artifact remains. No second candidate or auditor invocation is authorized under #03.

## Scope

No scientific result is established. The design, hypothesis, T0 HOLD and historical A1/A2 results are unchanged. Any local unit-test/CI result is source validation only and cannot upgrade this STOP. A future attempt requires a new explicit allocation and fresh freeze; no successor allocation is requested here.
