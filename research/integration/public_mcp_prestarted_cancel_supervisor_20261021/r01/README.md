# r01 captured execution

- Conditions: [`conditions.json`](conditions.json)
- Source fingerprints: [`source-hashes-at-run.txt`](source-hashes-at-run.txt)
- Normal Python: exit `0`, 105 tests, 41.262 s
- Optimized Python (`-O`): exit `0`, 105 tests, 41.280 s
- Sanitized public-MCP cases: `healthy-release.json`, `stale-generation.json`, `blocked-helper-deadline.json`
- stdout/stderr and exit codes: retained in the matching `.log` and `.exit` files

The exact r01 test-source snapshot is retained under `source-snapshot/`; its hash matches the test source fingerprint from the run. The separate summary and scope limits are in the parent [packet README](../README.md).
