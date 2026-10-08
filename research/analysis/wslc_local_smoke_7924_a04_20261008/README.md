# WSLc A04 — offline audit of retained A02 evidence

Successor to [Issue #8446 A03](https://github.com/Unjuno/agent-interface/issues/8446), tracked by [Issue #8455](https://github.com/Unjuno/agent-interface/issues/8455). This package is additive beneath its own path. The 17 imported A02 files are immutable evidence and match both A02's SHA-256 manifest and their Git blob identities from the recorded source commit.

## H / T / D / C / U

- **H:** A separately implemented auditor can validate the retained A02 result with its two different cleanup receipt shapes and reject four isolated corruptions without running A02/A03 code.
- **T:** Import and hash-check A02's exact 17 files; inspect the saved candidate cleanup's top-level `absence_verified` and auditor cleanup's exact-CID nested `targeted_inspect_checks` receipt; exercise fixture-digest, EROFS, external-call-count, and auditor-cleanup-presence mutations. Run local Python unit tests only while the shared WSLc owner gate remains closed.
- **D:** Local preparation validation: 8/8 tests pass on host Python, including all four mutation rejections, changed-input rejection, and SHA-256/Git-blob freeze validation. This is not the formal A04 result. The required one-shot WSLc audit is **HOLD / NOT RUN** until #7924 explicitly records owner reconciliation and exclusive-lane clearance.
- **C:** Host-side tests do not establish WSLc behavior, container isolation, or a formal WSLc audit. A02 recorded a cgroup/swap warning; its requested 512M is not an effective memory-cap claim.
- **U:** This audit-only package changes neither A02 nor A03's failed outcomes. It establishes no Docker parity, speed benefit, memory relief, hard limit, OOM prevention, GUI/model capability, or general migration claim.

## Reproduction and evidence

From this directory, run `python -B -m unittest -v test_audit` for preparation tests. This does not invoke WSLc and does not satisfy the formal pass gate in `PROTOCOL.json`. `auditor.py` independently verifies the A02 manifest and retained records; it never imports or executes A02/A03 auditor code. `FREEZE.json` binds the imported A02 SHA-256 values, source Git blob IDs, A04 source hashes, and source main SHA.

The formal WSLc invocation has not been made. Issue #7924's latest readiness record explicitly prohibits further WSLc CLI/RPC or WSL-management calls until existing client/container ownership is reconciled and the shared lane is explicitly released. A zero current process count would not clear that requirement. Do not run the formal invocation until that gate is updated on GitHub.

## Formal result

`HOLD_WSLC_OWNER_GATE`; no A04 WSLc invocation, CID, container, cleanup receipt, or `AUDIT.json` exists. No Docker or WSLc command was run for this A04 package. Do not represent the local unit-test pass as `PASS_AUDIT_ONLY_SCOPED`.
