# WSLc A03: independent audit of retained A02 evidence

Successor to [Issue #7924](https://github.com/Unjuno/agent-interface/issues/7924), tracked by [Issue #8446](https://github.com/Unjuno/agent-interface/issues/8446). A02's source, candidate result, failed auditor invocation, and cleanup receipts are copied byte-for-byte under `predecessor_a02/`; they are immutable historical evidence.

## H / T / D / C / U

- **H:** A separately implemented auditor can independently verify the saved A02 result, frozen identities, and scoped cleanup receipts, and reject malformed evidence without changing the historical outcome.
- **T:** Validate exact source hashes and Git blob identities for all 17 A02 package files; reconstruct candidate stdout/result, fixture digest, read-only `EROFS`, no external calls, exact container names/CIDs, `--rm` absence receipts, and the original auditor failure. Evaluate four isolated in-memory mutations in the same run.
- **D:** `PASS_AUDIT_ONLY_SCOPED` requires all imported bytes to match A02's frozen manifest and GitHub source identities, every saved-data check to pass, all four mutations to be rejected, and this one A03 auditor invocation to exit 0. Any failure is final; no retry.
- **C:** A02 retained only combined stdout/stderr. One host/runtime only. The historical WSLc output warns that cgroup swap limits are unavailable.
- **U:** This does not repair or upgrade A02's `FAIL_AUDITOR_CONTRACT`, rerun A02, or establish Docker parity, speed, memory relief, effective memory limits, OOM prevention, GUI/model behavior, or general migration.

## Execution result

**A03 result: `FAIL_AUDITOR_CONTRACT`.** The one frozen WSLc invocation exited 1 before completing the retained-evidence checks. The auditor expected `absence_verified` at the top level of the A02 auditor cleanup receipt, but A02 records that field under `targeted_inspect_checks[1]`. This is an A03 verifier defect; it does not contradict the saved A02 cleanup evidence and does not alter A02's `FAIL_AUDITOR_CONTRACT` result.

The single WSLc invocation used the pinned image with no network, read-only package mount, `--pull never`, and `--rm`. A warning stated that swap limits/cgroup support are unavailable, so the requested 512M is not evidence of effective memory isolation. One exact-CID inspect returned not found after auto-remove. No Docker operation, global container list, retry, A02 candidate run, or A02 auditor run occurred. Exact output and receipts are retained.

The A03 allocation is final and was not rerun. `AUDIT.json` is intentionally absent because the auditor did not finish. Any follow-up must be a distinct, explicitly scoped allocation and must not rewrite this outcome or the A02 evidence.
