# Construction source and reproduction

This is the corrected-contract successor to #4899. It preserves the predecessor's HOLD and raw bytes and does not reuse any formal seed or formal result. Source ancestry is the read-back source from PR #4906, adapted only for this successor's fresh allocation/seeds and corrected hash contract.

Before the construction data run, publish and read back `FREEZE.json`, `FREEZE.sha256`, all source files and this protocol from the additive branch. Compare SHA-256 bytes exactly. Create empty host output directories outside the source tree.

Zero-update tests:

```powershell
docker run --rm --pull=never --network=none --read-only --cpus=1 --memory=2g --pids-limit=64 --mount "type=bind,source=<source>,dst=/src,readonly" --workdir /src --env PYTHONDONTWRITEBYTECODE=1 sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e -m unittest -v test_construction
```

Excluded construction run and separate audit:

```powershell
docker run --rm --pull=never --network=none --read-only --cpus=1 --memory=2g --pids-limit=64 --mount "type=bind,source=<source>,dst=/src,readonly" --mount "type=bind,source=<raw-output>,dst=/out" --workdir /src --env NEEDLE_CONSTRUCTION_OUTPUT=/out --env PYTHONDONTWRITEBYTECODE=1 sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e -m construction
```

The pinned image entrypoint is Python, so use `-m construction`, not `python construction.py`. Run the independent audit as `-m construction_audit /in/construction_raw.json /out/CONSTRUCTION_AUDIT.json` in a distinct, read-only-raw/writable-report invocation. Preserve raw stdout/stderr and receipts. One construction invocation and one separate audit; no retries. Formal seeds are not run by this protocol.

