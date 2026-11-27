# Result — R01

**PASS_SYNTHETIC_FAILURE_USAGE_DURABLE_JOIN.** The two-test module passed 2/2 normally and 2/2 under `-O` on Windows CPython 3.13.14. Exit codes were 0 in both modes.

The new composition case drove the synthetic JSONL App Server client through `PersistentGroundingModel`, `V3PersistentGroundingAdapter`, `run_g10_in_durable_allocation`, and `audit_allocation()`. The intentionally invalid answer remained a failed attempt. The audit retained its exact turn/thread IDs, requested model/effort and all five usage counters, including cached-token subset semantics. Caller outcome was `CALLER_FAILED`; execution and effect receipts were absent. The pre-existing transport case also passed and verifies those identities/usage reach the v3 attempt ledger and are held by the comparison projection.

This closes one offline composition check only. The provider was a local protocol fixture, no GUI/native input ran, and no three-arm `ProspectiveRun` or live provider allocation was started. It supplies no #57 live efficiency, task success, recovery reliability, or preview graduation result.

Exact conditions and commands: [CONDITIONS.md](CONDITIONS.md). Raw output: [normal](normal.stderr.txt), [optimized](optimized.stderr.txt); process exit codes: [normal](normal.exitcode.txt), [optimized](optimized.exitcode.txt). Hashes are in [SHA256SUMS](SHA256SUMS).
