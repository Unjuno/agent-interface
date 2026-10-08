# WSLc A03: independent audit of retained A02 evidence

Successor to [Issue #7924](https://github.com/Unjuno/agent-interface/issues/7924), tracked by [Issue #8446](https://github.com/Unjuno/agent-interface/issues/8446). A02's source, candidate result, failed auditor invocation, and cleanup receipts are copied byte-for-byte under `predecessor_a02/`; they are immutable historical evidence.

## H / T / D / C / U

- **H:** A separately implemented auditor can independently verify the saved A02 result, frozen identities, and scoped cleanup receipts, and reject malformed evidence without changing the historical outcome.
- **T:** Validate exact source hashes and Git blob identities for all 17 A02 package files; reconstruct candidate stdout/result, fixture digest, read-only `EROFS`, no external calls, exact container names/CIDs, `--rm` absence receipts, and the original auditor failure. Evaluate four isolated in-memory mutations in the same run.
- **D:** `PASS_AUDIT_ONLY_SCOPED` requires all imported bytes to match A02's frozen manifest and GitHub source identities, every saved-data check to pass, all four mutations to be rejected, and this one A03 auditor invocation to exit 0. Any failure is final; no retry.
- **C:** A02 retained only combined stdout/stderr. One host/runtime only. The historical WSLc output warns that cgroup swap limits are unavailable.
- **U:** This does not repair or upgrade A02's `FAIL_AUDITOR_CONTRACT`, rerun A02, or establish Docker parity, speed, memory relief, effective memory limits, OOM prevention, GUI/model behavior, or general migration.

## Execution status

Pending frozen A03 audit invocation. The only permitted container operation for this allocation is one uniquely named, offline WSLc auditor run against this read-only package. No Docker or global container list is used.
