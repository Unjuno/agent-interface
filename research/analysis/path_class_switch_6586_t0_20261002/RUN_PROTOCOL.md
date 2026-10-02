# Formal run protocol

The frozen `run_candidate.ps1` and `run_auditor.ps1` scripts are the only formal launchers. Each checks the frozen main base, exact source and input hashes, cached image digest, distinct empty output directory, and one-shot receipt path before calling WSLc.

Candidate invocation: mount this package read-only at `/src`, mount `results/formal-01/candidate` read-write at `/out`, disable network and pulls, request 0.25 CPU and 512 MiB, run as UID/GID 65534, and execute `python -B /src/candidate.py --input /src/inputs.json --output /out/candidate.raw.json`.

Auditor invocation, only if the candidate exits 0: mount this package read-only at `/src`, mount `results/formal-01/candidate/candidate.raw.json` read-only at `/raw/candidate.raw.json`, mount `results/formal-01/auditor` read-write at `/out`, and execute `python -B /src/audit.py --input /src/inputs.json --oracle /src/oracle.json --raw /raw/candidate.raw.json --output /out/audit.json` under the same pinned runtime/limits. The auditor process/container is separate from the candidate.

Both scripts retain stdout/stderr and exit status. `--rm` removes only the invocation's own container. Never stop, remove, inspect by exec, or alter a different container. A nonzero stage, existing output, changed main/image/source, or resource-owner conflict is terminal for this allocation; no candidate/auditor retry.
