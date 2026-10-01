# Issue #3840 — Docker Desktop newline-frame replication

## Disposition

Primary scoped observation: `FAIL_FALSE_SUCCESS`. A caller that treats successful JSON parsing and `result.status == "completed"` as complete delivery accepted a valid-JSON strict prefix after the producer's terminal LF was removed.

Secondary scoped gate recorded by the formal runner: `PASS_FRAMING_GUARD_RECOVERY_SCOPED`. Terminal-LF framing rejects the delivered prefix. Read-only `attempt-status` and `review` recovered the exact retained report; the snapshot did not change, `replay_allowed` remained false, and dispatch stayed at one.

Evidence/provenance disposition: `HOLD_EVIDENCE_INCOMPLETE` for independent reproducibility of the audit/provenance chain. The original standalone audit output reports PASS with `errors: []`; the raw auditor digest matches the originally declared freeze digest. A later modified verifier was incorrectly compared against the original digest and its mismatch result is superseded. The substantive four-row claim is independently corroborated, but exact pre-run PLAN/auditor bytes were not preserved in an immutable committed snapshot for an independent rerun. The initial audit is not claimed to have failed, and is not represented as independently revalidated. No formal rerun was performed.

## Formal allocation

- Allocation: `issue3814-jsonl-frame-02`, successor/cross-engine replication for #3814 and #3834.
- Frozen base: `5842cea6b16dde275f79caef3f09fdba828112e0`.
- Environment: Docker Desktop 28.5.1, Linux/amd64, official Python platform digest `sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b`, network disabled, source/read-only root, bounded resources and dropped capabilities.
- Formal runner invoked once against the frozen `5842cea6` runtime source snapshot (not current main; later commits updated `runtime/cli_v1/api.py` and `test_cli.py`). It wrote four cases: complete-delivery positive control; terminal-LF loss; request-only unknown; occupied destination.
- Byte-level cross-check: producer accepted 336 bytes ending in LF; downstream delivered the exact 335-byte `accepted[:-1]` prefix. `json.loads` accepts the prefix and reports `result.status=completed`.
- Recovery cross-check: retained report SHA-256 is `9eb423c98a7b0d97ea22c5adeb3c7dbbe8c935bf65c42c7a2285203d7a5235be`; attempt-status and review both reference that SHA; before/after snapshots match; one dispatch; no replay.
- Immutable raw output: `C:\Users\junny\Documents\Codex\2026-09-21\issue-3840-formal-02\raw.json`, SHA-256 `457aa421e3f1f340a950632bc78a56548a0a5cc41e215a7afa59bfd613e1a806`.
- Initial audit output: `C:\Users\junny\Documents\Codex\2026-09-21\issue-3840-audit-02\audit.json`, SHA-256 `2a075d0337066526d3aa0b06ab823cb5e8398b57c1e5605d72ae9ae86313ec81`; it reports `PASS_AUDIT_NEWLINE_FALSE_SUCCESS_SCOPED`, four rows, and `errors: []`.
- Independent row-level cross-check output: `C:\Users\junny\Documents\Codex\2026-09-21\issue-3840-replay-audit-v2\crosscheck.json`, SHA-256 `70b0eeaca1751613f7ffa047dbb81fb3315ecbd343df05affd4387105d0cdd79`; Docker execution passes all listed raw invariants. This is supplementary and does not replace the preregistered auditor.
- The original auditor digest in raw evidence matches the declared freeze digest `1db4219...`. A later modified verifier (`974178...`) was incorrectly compared against it; that mismatch result is superseded. Exact original PLAN/auditor bytes were not preserved in an immutable committed snapshot for independent re-execution, so the separate provenance reproducibility gate remains HOLD. The initial audit is neither declared failed nor independently revalidated.

## Scope and limits

This is a synthetic local CLI boundary test, not real OS/network truncation, a live task, broad caller reliability, performance/token evidence, power-loss evidence, OrbStack parity, or product behavior. The result corroborates the exact terminal-LF case and retained recovery only. It does not close #3711 or #3808 and does not resolve the provenance HOLD.

Prior-art relation: #3834 (merged PR #3846) tested the same terminal-LF strict-prefix mechanism on OrbStack/linux-arm64. This allocation is a Docker Desktop/linux-amd64 replication, not a novel mechanism claim.
