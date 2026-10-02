# OrbStack runbook — one candidate, one independent auditor

The candidate source and fixture are read-only. Prepare two empty output directories, `results/candidate/` and `results/audit/`; keep Docker configs, inspect output and stdout logs under `execution/`, never inside those mounts before process entry.

Create the candidate container from the digest-pinned image with network disabled, read-only root, 1 CPU / 512 MiB configured / 64 PIDs, all capabilities dropped, no-new-privileges and uid 1000. Mount only the package read-only at `/allocation`, and `results/candidate/` writable at `/candidate-output`. Invoke `python /allocation/candidate.py /allocation/cases.json /candidate-output/candidate.json` exactly once. Capture the full file, exit code, SHA-256 and container state. If it fails or the file is absent, preserve STOP and do not run or retry.

Only after successful candidate capture, create a separate auditor container with the same isolation. Mount package and candidate JSON read-only, and `results/audit/` writable at `/audit-output`. Invoke `python /allocation/auditor.py /allocation/cases.json /candidate-input/candidate.json /audit-output/AUDIT.json` exactly once. Preserve stdout, receipt, exit code and state. No replacement run is permitted under T0b.
