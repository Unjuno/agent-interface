# WSLc A04: receipt-shape-specific audit of retained A02 evidence

Successor to [Issue #7924](https://github.com/Unjuno/agent-interface/issues/7924), following audit-only allocations [#8446 A03](https://github.com/Unjuno/agent-interface/issues/8446) and [#8455 A04](https://github.com/Unjuno/agent-interface/issues/8455). A02 remains `FAIL_AUDITOR_CONTRACT`; A03 also remains `FAIL_AUDITOR_CONTRACT`. Their source, outputs, and PRs are immutable historical records. A04 imports only exact A02 evidence and does not rerun A02 or A03.

## H / T / D / C / U

- **H:** A separately implemented auditor with distinct candidate/auditor cleanup schemas can validate the retained A02 evidence and reject four isolated mutations without changing either earlier result.
- **T:** Verify all 17 A02 files against manifest SHA-256 and Git blob IDs. Inspect the actual different cleanup-record shapes before freeze. In exactly one offline WSLc invocation, validate frozen identities, candidate JSON/stdout, fixture SHA, EROFS 30, zero out-of-scope calls, each scoped cleanup receipt, the original A02 audit failure, and four targeted mutations.
- **D:** `PASS_AUDIT_ONLY_SCOPED` requires all imports and saved data to validate, both cleanup formats to pass their specific validators, all four intended mutation checks to reject, the one formal A04 WSLc invocation to exit 0, and its exact CID to be absent after `--rm`. Any failure is final; no retry.
- **C:** A02 retained combined stdout/stderr and one-host WSLc behavior. A02 reported a kernel/cgroup swap-limit warning.
- **U:** A04 can only audit retained evidence. It cannot turn A02/A03 into passing allocations and establishes no Docker parity, speed, memory relief, effective limit, OOM prevention, GUI/model result, or general migration.

## Execution status

The separately scoped pre-freeze schema smoke runs only `preflight_receipt_shapes.py`; it checks the actual A02 cleanup JSON shape and CIDs, does not run an auditor, and cannot establish the audit hypothesis. After this smoke passes, freeze the auditor and execute exactly one formal A04 audit in WSLc. The formal run uses a separate unique container/CID and exact-CID-only cleanup verification.
