# Successor #4678 STOP evidence audit — Issue #4791

## H / T / D / C / U

**H.** The published #4678 bundle is independently self-verifying: all seven entries in its SHA256SUMS match, and the auditor accepts checkpoint absence only with retained host-cache inventory.

**T.** One formal local Docker invocation replayed the frozen bundle and auditor in `python:3.12-slim-bookworm` image `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e` (linux/amd64, network none, read-only root, 1 CPU, 512 MiB, 64 PIDs; all capabilities dropped; no-new-privileges). No GPU, model, host cache, package install, or network access. Formal invocation=1, runner exit=0. Exact stdout is retained in `FORMAL_OUTPUT.json`; frozen inputs/source are `FROZEN_BUNDLE.json`, `FREEZE.json`, and `audit.py`.

**Observed checksum rows.** The container computed different SHA-256 values for all seven file contents from the values listed in the frozen `SHA256SUMS`: README.md, COMMANDS.md, PREFLIGHT.json, audit.py, test_audit.py, AUDIT.json, VERIFICATION.json. Exact expected/observed pairs are in FORMAL_OUTPUT.json. The old bundle states checkpoint absence, but no raw cache inventory was retained; the published auditor's copied absence predicate accepts those three author-entered fields without any raw observation.

**D — disposition: `HOLD_AUDITOR_IMPLEMENTATION_DEFECT`.** The frozen verifier has an implementation defect in Git blob validation: its bytes literal uses a double-escaped `\\x00`, so it hashes the literal characters rather than Git's NUL delimiter. Consequently its Git-blob checks rejected every frozen input. The result selector also prioritizes checksum mismatches over these source-integrity errors, and the invocation returned exit 0. The 7/7 checksum discrepancies are a strong directly observed discrepancy in the MCP-fetched snapshot, but this formal run does not satisfy its own exact-source-integrity gate. Do not report an unqualified formal FAIL or PASS. The four mutation controls rejected (4/4), but did not cover this auditor defect. No rerun is made: the single allocation is consumed.

**C — controls.** Main snapshot commit `4fa120496342b9f955a6e6789d78ab308cc2c5a2`; source commit and Git blob identities are in FREEZE.json/FROZEN_BUNDLE.json. A prior exploratory probe saw the same concerns and is disclosed in the freeze; it is excluded from formal counts. Frozen bytes, #4678, and PR #4781 remain unchanged.

**U — limits.** This does not establish whether the frozen checkpoint actually existed or was absent on the original host, does not prove tampering, and says nothing about the invocation guard or model quality. Resolve only with a separately named successor that fixes the verifier, independently proves exact source bytes, and captures raw scoped cache inventory; do not reuse this consumed allocation.

## Reproduction and environment

The sole formal invocation executed the frozen `audit.py` bytes via `python -B -c` with FROZEN_BUNDLE.json on stdin in the cached image above. Docker was already running the unrelated Ollama container; this audit stayed CPU-only. The container image ID was inspected immediately before invocation. Exact formal output and full SHA rows are retained unchanged.
