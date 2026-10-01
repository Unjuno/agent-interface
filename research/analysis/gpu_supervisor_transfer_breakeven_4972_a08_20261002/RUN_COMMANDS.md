# One-shot Podman invocation from Arch WSL

Run only after the exact slot is explicitly released/assigned and every start gate passes. The exact image must already be present by digest. study is this frozen package directory; out is a new, separate directory.

Candidate (one invocation):

    image='docker.io/pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067'
    frozen_ref='pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067'
    study='/root/research/analysis/gpu_supervisor_transfer_breakeven_4972_a08_20261002'
    out='/root/research/outputs/gpu_supervisor_transfer_breakeven_4972_a08_20261002'
    test ! -e "$out" || { echo STOP_OUTPUT_EXISTS; exit 2; }
    mkdir -m 700 "$out"
    podman run --rm --pull=never --device nvidia.com/gpu=all --network=none --cpus=2 --memory=2g --pids-limit=128 --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m -e AI_IMAGE_REF="$frozen_ref" -e AI_OUTPUT_DIR=/out -v "$study:/study:ro" -v "$out:/out:rw" --workdir /study --entrypoint python "$image" runner.py
    candidate_exit=$?

Only if candidate exit is 0 and exactly one candidate_result.json exists, run the CPU-only raw auditor once (no CDI device):

    podman run --rm --pull=never --network=none --cpus=1 --memory=1g --pids-limit=64 --read-only --tmpfs /tmp:rw,nosuid,nodev,size=32m -e AI_IMAGE_REF="$frozen_ref" -e AI_CANDIDATE_PATH=/out/candidate_result.json -e AI_OUTPUT_DIR=/out -v "$study:/study:ro" -v "$out:/out:rw" --workdir /study --entrypoint python "$image" audit.py

No retries, substitutions, image pulls/builds, or second invocation. Retain exact stdout/stderr, exit codes, raw JSON, and audit receipt.
