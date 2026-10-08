# Issue #3816 — formal audit result

- Allocation: `issue3711-downstream-truncation-audit-v3-03`
- Disposition: **PASS_AUDIT_BINDING_SCOPED**
- GitHub Actions run: [35535734068](https://github.com/Unjuno/agent-interface/actions/runs/35535734068)
- Job ID: `106144309454`
- Audit source commit: `209fdb3db8e59b07adb8d4d03fcc7cccc08ab86a`
- Frozen evidence commit: `8bac49525c93835a69b6d441740a1c424faaecb2`
- Runner: GitHub-hosted Ubuntu 24.04 ARM64; Docker Engine 28.0.4 / linux/arm64
- Image: `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`
- Container: `--network none --read-only`, frozen inputs mounted read-only, unique empty output mount
- Construction tests: 4/4 passed
- Formal experiment invocations: 0; independent audit invocations: 1

The frozen baseline matched: raw SHA-256 `3f51dc5a4c9c8acb48fc2929a8219260575271e5794cd5bd4afedf6f712afc73`; accepted output 246 bytes / `e8ef9f6dd897325a22b1927d27e7fba2948051bb309cc472bbf2a1bfaba863d1`; delivered prefix 23 bytes / `0450145d98f8ff197766d91827a438db1aa5800d556b4bee24eb57b33e168d4a`.

Both predeclared corruption cases were rejected by the frozen receipts:

- Same-length `/out/attempt`→`/bad/attempt` accepted JSON remained valid but raised `ACCEPTED_SHA256_MISMATCH`.
- Truncating the delivered prefix from 23 to 22 bytes still left a strict, invalid JSON prefix, but raised both `DELIVERED_BYTES_MISMATCH` and `DELIVERED_SHA256_MISMATCH`.

Machine-readable result and original one-line auditor stdout are preserved adjacent to this report. The result SHA-256 is `e7bff711eb1a8407ea1335ea9da231e7a402dd3077debebddf94c2130153e672`.

Scope remains limited to integrity-binding checks on this synthetic retained record. No OS/network truncation, CLI recovery under fault, runtime reliability, or Issue #3711 closure is established. The earlier v3-01/v3-02 STOPs remain unchanged.
