# Formal run record — A02 auditor-only allocation

Allocation: `VERSION-DEFINED-6691-A02-AUDIT-20261003-01`

- Base main: `e52c4a65915cf48641c63cc95950be15f1b77cbf`
- Freeze commit: `a65705d29008e18bfeada078cbf6ac2bc4608f81`
- Candidate invocations: 0 (A01 retained candidate not rerun)
- Auditor invocations: 1/1; retries: 0
- Image: `python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, `linux/arm64`
- OrbStack machine: `agent-interface-6576-tailid-parity-a03-20261002`; private Docker Engine
- Container ID: `9c756d76f2645948c078d347e01c4c4f93238a3b46e8a26dc81f11458405cc8a`
- Exit: 0; `OOMKilled=false`; configured network none, read-only rootfs/source, 1 CPU, 256 MiB, 64 PIDs, dropped capabilities, no-new-privileges, user 65534:65534
- Auditor stdout summary: `{"disposition": "PASS_METHOD_SCOPED", "errors": [], ...}`; exact retained audit JSON is in `formal_01_20261003/audit.json`.
- Audit JSON SHA-256: `3354eb0c9e5dd4db5c9218a70ed09df7bef7cc889e8f94206c68806e22ecfbbf`
- Source/input hashes were checked in the OrbStack VM before launch and match `FREEZE.json`.

Exact formal command:

```text
docker run --name 6691-a02-auditor --network none --cpus 1 --memory 256m --pids-limit 64 --read-only --cap-drop ALL --security-opt no-new-privileges --user 65534:65534 --mount type=bind,src=/home/taka/6691-a02,dst=/src,readonly --mount type=bind,src=/root/6691-a02/out,dst=/out --workdir /src python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B /src/auditor.py /src/raw.json /src/candidate.json /out/audit.json
```

The A01 source, raw and candidate hashes are retained in `input_snapshot/`; A01 itself remains `STOP_AUDITOR_CONTAINER_LAUNCH`. No host-side auditor replay, candidate regeneration, GUI/model/user input, network access, or external effect occurred for A02.
