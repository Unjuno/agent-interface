# Frozen baseline source lineage

The original `SHA256SUMS` includes two repository-root paths whose content has since changed on current main:

- `research/live_control/executor_v13.py` at frozen base `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`: SHA-256 `5c54927e5087af42006c712ec906e2ec69e9155586730dee494dd3b5d43ced9a`.
- `research/live_control/test_executor_v13.py` at the same base: SHA-256 `6542eee9ecb37a7a01f90f97682f8d152a7156b4a3410e8a77fb6649ae9c50d4`.

Exact frozen bytes are retained under `baseline_source/`; the original manifest and report are unchanged. The other 19 manifest entries verify against the preserved paths. Thus all 21 declared digests verify when those two historical root paths are resolved to these frozen copies. This is custody of the historical baseline, not a claim that it equals current main or that the superseded interim repair is current code.
