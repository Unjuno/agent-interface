# Allocation-02 run protocol

Allocation: `TIMING-RECEIPT-6532-A02-20261002-01`.

## Preconditions

1. A named physical-host owner explicitly releases `unjuno-native-ci-6092`, and coordinator assigns one bounded CPU-only OrbStack slot; absence/idle CPU is not assignment.
2. Refresh current main and require the frozen base to equal the observed main SHA. Recompute every source/fixture/image digest and verify the unique output directory does not exist.
3. Run only the construction suite before formal; require every test pass. Reconfirm the source is read-only and output mount is distinct.
4. If any precondition fails, preserve STOP with candidate=0, auditor=0, containers=0. Do not request a rolling replacement slot.

## Pinned execution

Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, platform `linux/arm64`; cached image only, no pull/build. Network none, one CPU, requested 512 MiB (not a hard-cap claim), 64 PID ceiling, read-only root/source, uid 65534, disposable container, unique writable output directory.

Run candidate once:

```sh
docker run --rm --pull=never --platform linux/arm64 --network none --cpus=1 --memory=512m --pids-limit=64 --read-only --user 65534:65534 --tmpfs /tmp:rw,noexec,nosuid,size=16m -v "$PWD:/src:ro" -v "$OUT:/out:rw" -w /src python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/research/analysis/timing_receipt_6532_a02_20261002/candidate.py --fixture /src/research/analysis/timing_receipt_6532_a02_20261002/fixture.json --output /out/candidate.json
```

Only on exit 0, run independent auditor once in a second container:

```sh
docker run --rm --pull=never --platform linux/arm64 --network none --cpus=1 --memory=512m --pids-limit=64 --read-only --user 65534:65534 --tmpfs /tmp:rw,noexec,nosuid,size=16m -v "$PWD:/src:ro" -v "$OUT:/out:rw" -w /src python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/research/analysis/timing_receipt_6532_a02_20261002/auditor.py --fixture /src/research/analysis/timing_receipt_6532_a02_20261002/fixture.json --raw /out/candidate.json --output /out/audit.json
```

The source shows exact flags; the eventual RUN record must also retain expanded absolute paths, UTC invocation times, stdout/stderr, direct exit codes, actual container IDs, engine/image/platform identities, resource warnings, output hashes, post-run container inventory, and the independent audit. `--help` is safe because the parser exits before processing; do not call the candidate module's `main()` without required explicit paths.
