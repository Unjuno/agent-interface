# Formal run record

- Allocation: `MULTIFIDELITY-ROUTE-CONTRAST-6155-T0-20261002-01`
- Frozen base: `39cff8c45e3df04f1f7e98962b043c3fb0179ed2`
- Candidate invocation: **1**, exit **0**, retries **0**.
- Independent raw-only auditor invocation: **1**, exit **1**, retries **0**.
- Candidate container: `mf-cv-6155-20261002-a01-candidate` (`--rm`); auditor container: `mf-cv-6155-20261002-a01-auditor` (`--rm`). Both exited and were automatically removed.
- Host: macOS arm64 with OrbStack context `orbstack`.
- Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, `linux/arm64`.
- Isolation for both invocations: `--pull=never --network=none --cpus=1 --memory=1g --pids-limit=64 --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m --cap-drop=ALL --security-opt=no-new-privileges`; candidate source read-only; auditor source/raw read-only; separate output mount. No model, GUI, app, network, GPU, or physical input.
- Existing container `unjuno-native-ci-6092` remained running and untouched. No claim of a #5085 lease.
- Exact UTC start/end timestamps were not captured; not inferred after the run.

## Commands

Candidate (one invocation):

```sh
docker run --rm --name mf-cv-6155-20261002-a01-candidate --pull=never --platform linux/arm64 --network none --cpus=1 --memory=1g --pids-limit=64 --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m --cap-drop=ALL --security-opt=no-new-privileges --user "$(id -u):$(id -g)" --volume "$PWD/research/analysis/multifidelity_route_contrast_6155_t0_v1:/src:ro" --volume "$PWD/research/analysis/multifidelity_route_contrast_6155_t0_v1/runs/MULTIFIDELITY-ROUTE-CONTRAST-6155-T0-20261002-01:/out:rw" --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/candidate.py --output /out/candidate.raw.jsonl
```

Auditor (a separate one-shot container, run only after candidate exit 0):

```sh
docker run --rm --name mf-cv-6155-20261002-a01-auditor --pull=never --platform linux/arm64 --network none --cpus=1 --memory=1g --pids-limit=64 --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m --cap-drop=ALL --security-opt=no-new-privileges --user "$(id -u):$(id -g)" --volume "$PWD/research/analysis/multifidelity_route_contrast_6155_t0_v1:/src:ro" --volume "$PWD/research/analysis/multifidelity_route_contrast_6155_t0_v1/runs/MULTIFIDELITY-ROUTE-CONTRAST-6155-T0-20261002-01:/raw:ro" --volume "$PWD/research/analysis/multifidelity_route_contrast_6155_t0_v1/runs/MULTIFIDELITY-ROUTE-CONTRAST-6155-T0-20261002-01/audit:/out:rw" --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/audit.py /raw/candidate.raw.jsonl --output /out/audit.json
```

Formal command outputs were redirected without alteration to `candidate.stdout.txt`, `candidate.stderr.txt`, `auditor.stdout.txt`, and `auditor.stderr.txt` in this directory.

## Outcomes

- Candidate raw: 2,700 JSONL records, uncompressed **128,461,928 bytes**, SHA-256 `154d8b0e6a1ec319881b4e87795840a4f0e647e39f5d0984d124ca8e5d13e184`.
- Raw retention: losslessly compressed with `gzip -n -9`; `gzip -t` passed and decompressed bytes reproduce the raw SHA above. Compressed artifact is 60,515,898 bytes, SHA-256 `5e8e03eabe58809cc60bea0b69b61de8c08bffb77d70e4458f6f0093ffd9746c`. The redundant uncompressed working copy was removed only after this exact hash verification; the formal content remains recoverable byte-for-byte from `.jsonl.gz`.
- Auditor JSON: SHA-256 `0cea3a0afcefb87fed13f48b9860ca8a74fcab0742f0c9fadde0bd2b4e2f7871`; disposition `FAIL_METHOD_GATE`; 9 groups / 2,700 rows; one preregistered positive-control interval gate error.
- Candidate stdout/stderr SHA-256: empty-file digest `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` for both.
- Auditor stdout SHA-256 `922f9c7a83b65d49656f0dfecb3d72443370d5004589ce4080ce11d3261da245`; stderr is empty-file digest above.
- Full report, source, test, and run artifact checksums are in package-level `SHA256SUMS.txt`.
