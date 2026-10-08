# OrbStack reproduction protocol (not yet executed)

Allocation request: `NONREQUESTER-EXTERNALITIES-6026-T0-20261001-01`, requested 16:15–16:30 UTC. A request is not a lease. Do not run unless #5085 contains explicit authorization for this owner/allocation and the start gate below passes.

At the authorized start, re-read #5085, #6026, `origin/main`, this branch/path, all four frozen source SHA-256 values in `results/host-run-06/RUN.md`, and the shared OrbStack inventory. Confirm the current branch descends from the exact fetched main, all source hashes match, the cached image is the exact pinned linux/arm64 digest, and the candidate/auditor names are absent. Any discrepancy is a terminal pre-candidate STOP with no retry.

Use only `docker --context orbstack`, `--pull=never`, linux/arm64, network disabled, read-only root and source mount, one CPU, 256 MiB, 64 PIDs, all capabilities dropped, and no-new-privileges. Use separate uniquely named candidate and auditor containers. Candidate stdout/stderr and exit status are retained before any auditor call. Run the auditor exactly once only after candidate exit 0. Inspect and remove only the two exact containers created by this allocation; never clean up an unowned container.

Candidate invocation (the output directory must be created before opening the output file):

```sh
docker --context orbstack run --name nonrequester-6026-t0-a01-candidate --pull=never --platform linux/arm64 --network none --read-only --cap-drop=ALL --security-opt no-new-privileges --pids-limit=64 --memory=256m --cpus=1 --mount "type=bind,src=$PWD,dst=/study,readonly" --workdir /study --entrypoint python python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f -B candidate.py fixture.json
```

Capture that command's stdout as `results/container-run-01/raw.json`, stderr separately, and the actual exit status in the run record. If and only if it exits 0, run the same hardened container contract under a different name with command `-B audit.py fixture.json results/container-run-01/raw.json`, capturing its stdout/stderr and exit status. No image pull/build, network, model, GUI, input, app, participant, or external notification is in scope.
