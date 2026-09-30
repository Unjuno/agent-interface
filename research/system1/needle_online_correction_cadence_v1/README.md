# Needle online correction cadence v1

Research-only comparison of immediate single-example LoRA updates with true two-example microbatch updates. No runtime code or product behavior is changed.

## Reproduce

1. Verify the exact image ID and source hashes in `FREEZE.json`.
2. Run the construction suite in the pinned CPU image (it performs zero optimizer updates):

   ```powershell
   docker run --rm --pull=never --network=none --read-only --cpus=1 --memory=2g --pids-limit=64 --security-opt=no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=64m --mount "type=bind,source=<source-dir>,dst=/src,readonly" --workdir /src -e PYTHONDONTWRITEBYTECODE=1 sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e -m unittest -v test_construction
   ```

3. Construction-only seeds 734011, 734012, 734013 and 734014 are excluded from formal evidence; 734014's complete raw is separately replayed by `construction_audit.py` in a second container. See append-only Issue amendments for each disposition.
4. For the original one-shot formal execution, use `formal.ps1` with a newly created empty output directory. Do not rerun the allocated seeds. The runner refuses an absent/wrong seed block or non-empty raw-output directory before training.
5. Reconstruct and audit from the preserved raw bytes using the pinned image and `audit.ps1` / `audit.py`. The auditor imports neither the runner nor its model classes and checks the actual retained log bytes against the invocation receipt.

The output contains the complete per-arrival prediction curves, adapter/optimizer states and raw input rows. Container logs are persisted as bytes and their manifest hashes those exact retained bytes. Scoped result only; update-only timings are not request-to-ack latency.
