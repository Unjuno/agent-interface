# Needle role-skill C support-count successor (#4749)

This allocation tests one narrow System-1/Needle question: does increasing role C's support set from 16 to 64 improve synthetic LoRA role-skill generalization while preserving the 16-row prefix and all paired controls?

## Status

- Construction seed 7865001 ran in Docker and passed independent audit.
- C accuracy: control16 0.954834; treatment64 0.962646 (+0.007812). A/B were exactly unchanged.
- The single construction point is not formal evidence and is below the preregistered >=0.01 paired-mean gate.
- Formal seeds 7865101–7866001 remain unused. No formal freeze or result is claimed.
- Historical Issues #4580 and #4619 are preserved; this is a separately allocated successor.

## Reproduce checks

Pinned image: needle-pilot05:local, sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e, linux/amd64.

```sh
docker run --rm --pull=never --platform linux/amd64 --network none --read-only --cpus=1 --memory=2g --pids-limit=64 --security-opt=no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=64m -v "$PWD:/work:ro" -w /work --entrypoint /usr/local/bin/python needle-pilot05:local -B -m unittest -v
```

Ten offline contract, corruption, seed-stream, preflight-gate, and independent-replay tests pass. The image lacks NumPy; PyTorch's warning is non-fatal and these CPU paths do not use NumPy.

## Formal boundary

See ISSUE_CONTRACT.md, PREREGISTRATION.md, formal.py, and audit_formal.py. Formal execution requires exact GitHub source/contract/freeze readback and current collision checks. One orchestration only; never retry or replace seeds.

This synthetic data-only package has no GUI, provider, user-data, or actuator authority. It does not establish live real-time learning, Astra supervision, concurrent robustness, broad transfer, or product readiness.
