# Frozen protocol — Issue #6590 mutation challenge v1

Scientific base main: `ce89f11fcff33b83de4a9b9ded7b89bf764b5f09`. This is an additive successor allocation; do not modify predecessor raw/audit/freeze.

Use the immutable local Docker image `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`. Every invocation must use `--pull=never --network=none --read-only`, mount sources read-only, mount only the dedicated output directory writable, and use `-B`. No shared container is entered or changed.

Formal cardinality: candidate CLI once, clean auditor CLI once, mutation challenge once (the challenge calls the auditor exactly once on one corrupted table, using the retained clean audit as its baseline), retries 0. Total formal auditor executions: two (one clean CLI, one mutation API call). No model fit, GPU, GUI, effects, or network.

Commands, from repository root (set `PKG=research/analysis/spatial_block_position_6590_t0_20261002` and `OUT=$PKG/mutation_challenge_v1/results`):

```sh
docker run --pull=never --rm --network=none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m -v "$PWD/$PKG:/src:ro" -v "$PWD/$OUT:/out:rw" python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /src/candidate.py --fixture /src/fixture.json --output /out/raw.json
docker run --pull=never --rm --network=none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m -v "$PWD/$PKG:/src:ro" -v "$PWD/$OUT:/out:rw" python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /src/auditor.py --fixture /src/fixture.json --raw /out/raw.json --output /out/AUDIT.json
docker run --pull=never --rm --network=none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m -v "$PWD/$PKG:/src:ro" -v "$PWD/$OUT:/out:rw" python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /src/mutation_challenge_v1/challenge.py --fixture /src/fixture.json --raw /out/raw.json --clean-audit /out/AUDIT.json --output /out/MUTATION_AUDIT.json
```

Run the small pytest-free unittest suite locally before freezing; do not rerun the three formal invocations after freeze. Preserve full stdout/stderr, exit status, timestamps, Python and image digest, raw/clean-audit/mutation-audit hashes. Any nonzero formal step is terminal for this allocation.
