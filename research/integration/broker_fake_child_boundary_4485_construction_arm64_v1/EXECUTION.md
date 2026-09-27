# Executed result — Issue #5013 ARM64 construction

**Disposition:** `PASS_REAL_FAKE_CHILD_NONZERO_CONSTRUCTION_SCOPED`. This result covers exactly one ARM64 fake-child exit-23 case. It consumes **0** of Issue #5013's frozen seven-case linux/amd64 allocation.

## Observed

- Container: cached `python:3.12-slim-bookworm`, image config `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, `linux/arm64`; Python 3.12.14, machine `aarch64`.
- Docker client/server: 29.5.2 / 29.4.0; Docker server `linux/aarch64` on OrbStack.
- Broker input Git blob: `5734f54f318db9ac5e96b2bed6f6bed105ac39ff`; SHA-256 before/after: `e44822269b921aa6327563b27e48a6d8ef4ebe35a182f50de541cf66fce6199c`.
- One request, one child call witness; fake child intended exit 23. Broker process and broker receipt both report 23. Child stdout `partial fake-child response\\n` was retained as broker response; child stderr `fake child diagnostic\\n` was retained in the receipt. Broker stdout/stderr were empty. Authority remained false.
- Runner wall time: 1,887,893,597 ns. No model/provider executable, network, GUI, credentials, or application effect was used.
- Independent second-container raw-only audit imported neither runner nor broker: zero errors; all 8/8 copied-result corruptions rejected. Raw SHA-256: `76eaee928ae0b00f52312bb9b47cbbb6d78df2e548e7dff4f0560a4922749161`; audit SHA-256: `18c300f472cb48d9667c89ccab9ef90a54084d42dfbd0ae507476557d1ca5d58`.

## Execution and validation record

Exactly one runner invocation and one separate auditor invocation, each with `--pull=never --platform=linux/arm64 --network none --read-only`, no-new-privileges, all capabilities dropped, 0.25 CPU, 256 MiB, 32 PIDs, and bounded 32 MiB tmpfs. Runner input/source mounts were read-only and only its fresh output mount was writable. Auditor saw raw output read-only and wrote to a separate audit mount. Both containers used `--rm`; no retry was made.

The exact commands are preserved in [PLAN.md](PLAN.md). Runner and auditor syntax preflight passed before invocation. The auditor's raw gate passed in the independent container. The current workspace is not a checkout of this repository and no production source changed, so the full repository CI suite was not run here; PR checks remain the integration gate.

## Limits

This is a construction PASS, not formal #5013 acceptance. It does not establish AMD64 behavior or any of the other six cases (exit 0, timeout, missing executable, malformed request, idle `--once`, or two queued requests). It proves no real Codex/model/provider behavior, GUI/task effect, latency, runtime authority, cross-architecture equivalence, or product claim. The seven-case formal allocation remains unconsumed.
