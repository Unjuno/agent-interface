OBSTAC FORMAL ALLOCATION 02 — `STOP_FAKE_EXECUTABLE_MOUNT_MISSING`

Current-main source was frozen at `c83ddb057c680a126144d000bf7ef7ba2274652a` (broker Git blob `f307daafdfd36d1ab4faf39bb36c36350e6e67e4`, SHA-256 `034b2e72a28fc3defb1b48195a2a8d3450e850895a4b3b7b7919dca44e198775`). OrbStack 29.4.0, linux/arm64, pinned `python:3.12-slim` image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; network none, read-only root/source, bounded CPU/memory/PIDs, no capabilities, no credentials, no real model/provider/GUI calls.

The seven-row matrix completed, but the formal container mounted the checkout only at `/repo`, while the frozen fake executable path was `/study/fake_codex.py`. Fake invocations were therefore zero. The independent raw-only audit ran in a second isolated container and reports `HOLD_AUDIT_ERRORS errors=9 files_hashed=41`. The raw receipts establish the mount mismatch; this is infrastructure/provenance STOP, not scientific PASS or FAIL for zero-exit propagation.

Narrow observations retained: explicit unavailable executable produced the typed unavailable receipt; malformed input failed closed with exit 1 and no broker receipt; `--once` with no request remained idle until the 300ms external bound; two queued requests produced only the `queued-a` response/receipt while `queued-b` remained queued, but child provenance failed. All raw requests, receipts, process records, auditor findings, and hashes are in `research/integration/issue_3924_orbstac_broker_contract_v1/formal_run_02/`.

Pre-case runner STOP from allocation 01 is also retained. No formal case is repeated under either allocation. The complete evidence bundle is being submitted via a separate PR for independent review and integration.
