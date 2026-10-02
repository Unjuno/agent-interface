# One-shot Podman invocation from Arch WSL

These commands describe the frozen Podman allocation only. Run them only after a coordinator assigns a non-overlapping slot, the prior owner explicitly releases it, and every gate in PREREGISTRATION.md passes. The pinned image must already be present in rootful Podman by digest; do not substitute the separate WSLc image cache. No command was run for allocation-08.

Candidate (one invocation; preserve both output streams and exit code on failure):

    image='docker.io/pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067'
    frozen_ref='pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067'
    study='/root/research/analysis/gpu_supervisor_transfer_breakeven_4972_a08_20261002'
    out='/root/research/outputs/gpu_supervisor_transfer_breakeven_4972_a08_20261002'
    test ! -e "$out" || { echo STOP_OUTPUT_EXISTS; exit 2; }
    mkdir -m 700 "$out"
    set +e
    podman run --rm --pull=never --device nvidia.com/gpu=all --network=none --cpus=2 --memory=2g --pids-limit=128 --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m -e AI_IMAGE_REF="$frozen_ref" -e AI_OUTPUT_DIR=/out -v "$study:/study:ro" -v "$out:/out:rw" --workdir /study --entrypoint python "$image" runner.py > "$out/candidate.stdout.txt" 2> "$out/candidate.stderr.txt"
    candidate_exit=$?
    printf '%s\n' "$candidate_exit" > "$out/candidate.exit.txt"

Only if candidate exits 0 and exactly one candidate_result.json exists, run the separate CPU-only raw auditor once without a CDI device:

    podman run --rm --pull=never --network=none --cpus=1 --memory=1g --pids-limit=64 --read-only --tmpfs /tmp:rw,nosuid,nodev,size=32m -e AI_IMAGE_REF="$frozen_ref" -e AI_CANDIDATE_PATH=/out/candidate_result.json -e AI_OUTPUT_DIR=/out -v "$study:/study:ro" -v "$out:/out:rw" --workdir /study --entrypoint python "$image" audit.py > "$out/auditor.stdout.txt" 2> "$out/auditor.stderr.txt"
    auditor_exit=$?
    printf '%s\n' "$auditor_exit" > "$out/auditor.exit.txt"

Retain exact stdout, stderr, exit codes, raw JSON, and audit receipt. No retries, substitutions, image pulls/builds, or second invocation within a consumed allocation.
