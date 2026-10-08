# WSLc A04 preparation report

## Disposition

**HOLD_WSLC_OWNER_GATE — formal A04 not run.** The separately implemented host-side auditor is locally tested against retained A02 evidence, but Issue #7924 still requires explicit WSLc client/container owner reconciliation and exclusive-lane release. Issue #7924's latest continuation explicitly says no further WSLc CLI/RPC or WSL management calls until that condition is recorded. This report preserves that boundary.

## Offline preparation

- Source main verified against `origin/main` immediately before branch creation: `44cae8f802ca1109dd03a5627fb3073bcc3c55cc`.
- Imported A02 inventory: 17 files; all manifest SHA-256 checks and all 17 source Git blob IDs matched before A04 changes.
- A04 auditor: separately implemented; does not import or execute predecessor auditor code.
- Host-Python unit tests: 8/8 pass in both normal and optimized mode. They validate both cleanup receipt shapes, reconstruct A02's recorded auditor failure, reject four targeted mutations, and reject modified imported evidence or Git-blob identity.
- WSLc/Docker commands, container invocations, image pulls, CID inspections, and WSL lifecycle operations for A04: zero.

## Required continuation

Do not run the formal command until #7924 records explicit owner reconciliation and shared-lane clearance. If that condition is met, re-check current main and this branch's freeze; then perform exactly one offline WSLc invocation under the frozen Issue #8455 protocol. The first formal outcome is final; no retry. Record any preflight HOLD or formal result without changing A02/A03 evidence.

The offline pass is preparation evidence only. It does not establish WSLc execution, Docker parity, speed, memory relief, hard memory enforcement, or OOM prevention.
