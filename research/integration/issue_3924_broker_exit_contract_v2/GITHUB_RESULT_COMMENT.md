## FORMAL ALLOCATION RESULT — `STOP_AUDIT_IMPLEMENTATION_MISMATCH`

The one frozen seven-case OrbStack formal matrix completed. The fake mount/source preflight passed in the actual formal container. Raw `exit0` shows child receipt returncode 0 while the broker exits 1; `exit23` propagates 23; timeout and intentional unavailable-executable receipts are typed; malformed input exits 1 without a receipt; no-request `--once` is idle until the 300 ms outer bound; and two queued requests produce one `queued-a` receipt/response/fake invocation.

The separate raw-only auditor inspected 50 retained files but returned `STOP_AUDIT_PROVENANCE` with one error: it expected timeout fake `sleep_s=0.3`, while the frozen FREEZE declares 2.0 and the raw invocation records 2.0. The frozen auditor is not rerun, and no scientific PASS/FAIL is promoted because its required audit gate failed. All raw and stdout are retained under `research/integration/issue_3924_broker_exit_contract_v2/formal_run_01/`.

A separate successor will independently audit the immutable raw files. No broker code or formal case is rerun here.
