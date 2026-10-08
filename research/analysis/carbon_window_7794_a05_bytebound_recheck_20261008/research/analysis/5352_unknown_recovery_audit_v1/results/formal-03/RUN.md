# Formal-03 run receipt

- Candidate invocation: `docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --pids-limit 64 --memory 256m --cpus 1 issue5352-hysteresis-audit:formal03`; exit 0; traversed 299,592 traces.
- Auditor invocation: `docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --pids-limit 64 --memory 256m --cpus 1 --entrypoint python issue5352-hysteresis-audit:formal03 /audit/audit.py`; exit 0; traversed 299,592 traces.
- Image: locally built from `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; final image manifest list SHA-256 `13d84b8466a28120cec2a2e69a4196937638de8253ead4263a48bb6c653ba54d`.
- Context: Docker Desktop `desktop-linux`; build used `--network=none`. Runtime root filesystem read-only, all Linux capabilities dropped, no-new-privileges, pids 64, 256 MiB, 1 CPU.
- Candidate result SHA-256 (UTF-8): recorded in `candidate.json`; independent audit result SHA-256 (UTF-8): recorded in `audit.json`.
- Disposition: `STOP_AUDIT_SEMANTIC_MISMATCH`; process exits 0 indicate completed enumeration, not scientific agreement.
