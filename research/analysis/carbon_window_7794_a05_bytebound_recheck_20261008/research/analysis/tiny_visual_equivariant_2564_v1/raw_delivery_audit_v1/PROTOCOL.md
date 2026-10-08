# H/T/D/C/U — #4814 raw-bundle delivery audit

Allocation: `tiny-visual-equivariant-raw-delivery-4814-20260928-01`
Parent experiment: `tiny-visual-equivariant-cnn-2564-20260927-01`
This is a raw-evidence delivery audit only, not a rerun of the consumed formal experiment.

## H — hypothesis

The exact 847,667-byte ZIP retained after the original #4814 Docker run is byte-identical to the archive metadata in the merged #4819 manifest, and its 16 members exactly reconcile to the published per-file byte lengths and SHA-256 values, including the validated predictions digest.

## T — bounded test

One local, CPU-only Docker invocation reads the original ZIP and the exact current-main `MANIFEST.json`. Verify archive byte length/SHA-256, ZIP CRCs, exact member set/count, each member length/SHA-256, expanded byte total, and `predictions.jsonl` digest. Produce one JSON audit receipt. No extraction to host, model load, training, fitting, seed use, GUI, network, or modification of original files.

## D — decision

Pass only as `PASS_RAW_BUNDLE_RECONCILES_MANIFEST` if every registered archive and member check matches. Otherwise preserve the observed mismatch as `STOP_RAW_BUNDLE_AUDIT`; no repair/retry or formal rerun.

## C — controls

Pin the already-cached image by immutable ID (`sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`, linux/amd64). Use `--pull=never`, `--network none`, read-only root and read-only source/manifest/archive mounts, with only a fresh output mount writable; 0.25 CPU, 256 MiB, 32 PIDs, dropped capabilities, no-new-privileges. Hash and byte-check the source, manifest, and raw archive before invocation. One invocation, zero retries.

## U — limits

A pass establishes repository-deliverable raw-byte integrity only. It does not rerun or change the original CNN/MLP fits, negative efficacy decision, or any model/vision claim. It does not establish scientific reproducibility beyond the registered synthetic data and hashes.

