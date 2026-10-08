# Posthoc independent matrix audit v2 (not a new study allocation)

## Reason for this audit

The frozen study and `audit.py` remain byte-identical. Post-run review of the retained v1 audit showed it compared `direct`, `compiled`, and `oracle` strings copied into RESULT rather than independently deriving the frozen policy output. This audit-only successor recalculates all expected actions and enumerates the exact finite state set from the already frozen PLAN. It does not rerun or alter the study, candidate, output, or decision gate.

## H / T / D / C / U

- **H:** An independently authored verifier can reconstruct all 256 expected decisions from the frozen policy description, match the exact Cartesian state set, verify the retained source/result identities, and reject ten predeclared copied-result corruptions.
- **T:** Run `audit_v2.py` once in the exact pinned Docker image, network disabled, read-only source/root, bounded CPU/memory/PIDs. Read only the original frozen sources and `formal01/RESULT.json`; write only a fresh v2 audit output. No study, candidate code, model, GUI, or input action is invoked.
- **D:** `PASS_INDEPENDENT_MATRIX_AUDIT_SCOPED` iff all 256 unique expected states exist, v1 runner fields independently equal the reconstructed policy outputs, source/result/auditor identities match, and all ten corruption controls reject. Any mismatch is FAIL. Even on audit PASS, the overall allocation remains `HOLD_ACTIVE_SNAPSHOT_RECEIPT_MISSING`, because original raw evidence contains no before/after active bytes/digests.
- **C:** This audit uses a separate implementation that imports none of the runner, candidate compiler, candidate policy, or original oracle. Mutations occur only in memory and are never written over raw evidence.
- **U:** It can independently verify only the finite matrix encoded in the original RESULT. It cannot retroactively establish actual ACTIVE snapshot preservation; the missing activation receipt requires a fresh, separately frozen future study if that question remains relevant. No timing, model, GUI, integration, or product claim.

## Frozen inputs

- Original intake main: `89ca30f756704c9e378fc2cdde90a03c6a569c03`.
- Original frozen package commit: `222d614d390c8f444b452bdaaa1e61410e84f5d6`.
- Original raw result SHA-256: `0d6c75e32d1efa6a2b365df0bccf6b100d197dbd8c157879bfd9db9cdd643f71`.
- New v2 audit source is SHA-pinned in `AUDIT_V2_FREEZE.json` before its one invocation.
- Image: `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64; no pull; no network.
- Command: `python -B /study/audit_v2.py --freeze /study/AUDIT_V2_FREEZE.json --result /results/RESULT.json --output /out/AUDIT_V2.json`.

This is an audit-only successor; original RESULT.json and AUDIT.json stay unchanged.
