# MAP01 terminal-sync artifact re-audit — T1 result

Disposition: **PASS_RAW_ARTIFACT_INTEGRITY_PARTIAL_SCOPE**; scientific classification **RECOVERY_TERMINAL_NOT_IDENTIFIABLE**.

## H / T / D / C / U

- **H:** The archived allocation-04 sidecar might contain event objects despite not being valid line-delimited JSON. A hash-pinned structural parse can determine which terminal events were actually retained.
- **T:** Downloaded GitHub Actions artifact `10592018768` for run `35470604368` without executing its contents. Checked its full ZIP SHA-256 against GitHub artifact metadata and the target member SHA-256 against the artifact's own result manifest. Parsed the exact member in memory with the frozen auditor. Construction tests used synthetic byte strings only.
- **D:** Full artifact ZIP was 4,091,131 bytes and SHA-256 `c688ac74883b014c6e614913866dc8e1afb01b208a9cd3a56e05fc024d33e9e1`, matching GitHub metadata. The 35,028-byte target sidecar SHA-256 was `9a26ee337c9fb3795dbc2a51f132d0dc8e014b6f01c9ceb1724d5eadaf3fe22f`, matching `result-sha256sums.txt`. The auditor reconstructed 45 JSON objects. Both retained COAST terminal rows (prelude and fallback) had verified-empty release receipts. This artifact contains one `coast_control/session-events.jsonl` member and no recovery-arm trace or recovery terminal. The sidecar is **not JSONL**: its writer used a literal `\\n` string between serialized objects. The exact runner blob at the execution head was `f5caf71a743a563b7de046b82d44db7ebe49e829`, and its `trace.write(...)` line has that writer expression.
- **C:** Missing recovery trace can mean the failed arm's files were not packaged; it does not prove that a recovery terminal was never emitted. A structural parser can recover this artifact, but ordinary JSONL consumers cannot parse the sidecar as separate records. The serialization defect affects diagnostic auditability, not the already retained controller event files or MAP01 outcome.
- **U:** The cause of the original fallback-terminal timeout remains undetermined. No recovery-arm terminal, efficacy, physical input, useful outcome, or new formal allocation is inferred. This posthoc re-audit does not satisfy the live recovery gate.

## Execution record

- Construction: `python -m unittest -v test_audit_trace.py` — **5/5 passed**.
- `python -m py_compile audit_trace.py test_audit_trace.py` — **passed**.
- `git diff --check` — exit 0; it emitted only the existing unrelated LF-to-CRLF warning for `research/analysis/README.md`.
- One raw-only audit invocation: `python audit_trace.py --artifact <downloaded artifact ZIP>` — exit 0.
- Formal candidate / recovery runner / workflow dispatch / retry: **0**.
- Container / game / model / GUI / input: **0**. This was an artifact-only CPU parse. Docker Desktop service was Stopped/Manual and the CLI did not respond; no lease was transferred, so no container was launched.

## Provenance and retained files

- Repository main observed before audit: `ad123c3875d81ebdc8bdfbdb59340005d705a60d`.
- Execution head for runner source inspection: `d30776888c3bd88cc6652743d678864d05a2edad`; runner Git blob `f5caf71a743a563b7de046b82d44db7ebe49e829`.
- Artifact: `map01-terminal-sync-diagnostic-3211-v4-35470604368`; GitHub artifact ID `10592018768`; workflow run `35470604368`.
- Machine-readable report: `AUDIT.json`.
- Exact parser/auditor: `audit_trace.py`; construction tests: `test_audit_trace.py`.
- Source hashes are recorded in `SHA256SUMS`.
