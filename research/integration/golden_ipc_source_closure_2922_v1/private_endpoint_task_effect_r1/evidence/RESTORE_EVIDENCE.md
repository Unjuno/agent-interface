# Restore the #4924 raw evidence archive

The archive was split into ordered 8 KiB binary Git blobs to keep each GitHub MCP blob within a small transport limit. After checking out this branch, from the repository root:

```sh
cat research/integration/golden_ipc_source_closure_2922_v1/private_endpoint_task_effect_r1/evidence/raw-evidence-01.tar.gz.part* > /tmp/raw-evidence-01.tar.gz
shasum -a 256 /tmp/raw-evidence-01.tar.gz
tar -tzf /tmp/raw-evidence-01.tar.gz
```

The expected SHA-256 is `49a28fb2a9a84414c10cbf843bef36aa256942bcaad0e9465e16adfef2bad7fd`. The glob's lexical ordering gives `partaa` through `partbi` (35 parts total). Inside the archive, run `shasum -a 256 -c SHA256SUMS` from the extracted directory to verify the formal runner outputs. `PUBLICATION_MANIFEST.json` additionally lists every archived file, including the independent `AUDIT.json` that was generated after the runner's SHA256SUMS.
