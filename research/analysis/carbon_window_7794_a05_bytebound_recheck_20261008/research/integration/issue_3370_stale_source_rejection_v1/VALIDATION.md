# Validation record

Sealed source tree: main `21425ed43b55d7eeb1b608d2e127c9fab7f6acc8`.

Before allocation, the v3 freeze check compared 14 source/preregistration
SHA-256 values, the command-spec SHA-256, the exact main commit, and the local
OrbStack image ID/platform. All matched; no mismatch was accepted.

Formal command: `evidence/container-command-v3.json`. OrbStack container
`issue-3370-stale-source-v3` exited 0 (full inspect record in
`evidence/stale_source_v3/container-result.json`). The independent audit was
executed inside the same pinned image with network disabled and read-only root;
it returned `PASS_STALE_SOURCE_REFUSED_ZERO_INPUT` with an empty failure list.

The following existing test programs were run inside the same pinned image,
with a private writable `/tmp` and read-only source mount:

```sh
/opt/mcp/bin/python research/live_control/test_native_mcp_v1.py
/opt/mcp/bin/python research/live_control/test_native_finish_after_v1.py
/opt/mcp/bin/python runtime/core_v1/test_contract.py
/opt/mcp/bin/python runtime/backends/x11_v1/test_text_plan.py
```

Results: 6 + 18 + 18 + 6 = 48 tests passed. Manifest verification recomputed
all 159 entries; no missing file, byte-count discrepancy, or SHA-256 mismatch.
