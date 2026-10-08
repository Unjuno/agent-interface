# Allocation 12 — one-shot WSLc commands

Run only within the owner-assigned interval recorded in #5085, after refreshing the owner log, exact main, source/data/image hashes, output absence, WSLc container inventory, and GPU process/utilization state. Candidate ceiling 1; raw-only auditor ceiling 1 and only after candidate exit 0; retries 0.

Image: `pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067` (linux/amd64). Use `wslc.exe run --rm --pull=never --network none --cpus 2 --memory 2g --gpus all` with read-only `/study`, separate writable `/out`, and record exact WSLc warning/cgroup output. Then one CPU-only audit container with no GPU and the same read-only source plus candidate output mounted read-only if supported. Never retry or substitute a seed.
