# MAP01 terminal-sync artifact re-audit — T1

Status before audit: frozen posthoc/raw-only audit; no live allocation.

## H / T / D / C / U

- **H:** The retained #3211 allocation-04 artifact contains only the coast-arm session trace, and its `session-events.jsonl` sidecar may not be line-delimited JSON despite its filename. A hash-verified parser can reconstruct its objects without changing the archive and determine whether any recovery terminal was retained.
- **T:** Read GitHub Actions artifact `10592018768` from run `35470604368`. Verify the exact session-trace bytes against `evidence-manifest/result-sha256sums.txt`; parse the trace without extraction or mutation; count arm-specific trace members and terminal rows. Construction tests use synthetic byte strings only. Run this raw-only auditor once. No candidate, retry, Docker/OrbStack, game, model, GUI/input, or workflow dispatch.
- **D:** Audit integrity passes only if the manifest pin matches, every event object parses, and observed terminal records satisfy the declared per-row checks. Scientific classification is `RECOVERY_TERMINAL_NOT_IDENTIFIABLE` if the archive has no recovery-arm event stream; absence from this artifact is not proof that the recovery event was never emitted.
- **C:** Workflow artifact packaging may omit failed-arm files; the child may have emitted an event not retained by the runner; a malformed sidecar encoding can be reconstructed by a structural JSON decoder but is still a format-contract defect for ordinary JSONL consumers.
- **U:** No diagnosis of the original timeout cause, no recovery efficacy, and no authorization or consumption of a formal recovery allocation.

## Frozen input identity

- Repository snapshot observed immediately before the one-shot audit: `ad123c3875d81ebdc8bdfbdb59340005d705a60d`.
- Workflow run: `35470604368`; artifact ID: `10592018768`.
- GitHub-recorded artifact digest: `sha256:c688ac74883b014c6e614913866dc8e1afb01b208a9cd3a56e05fc024d33e9e1`.
- Target member: `results-local/doom/map01-terminal-sync-diagnostic-3211-04/pair-01/coast_control/session-events.jsonl`.
- Expected scope: raw artifact integrity and retained event structure only.

## Frozen local audit source hashes (SHA-256)

- `audit_trace.py`: `ED8181F75C3799A8EDA4FD50C006FF4E3A8D591DFCC6FAF810EEFF3AC3F4F99E`
- `test_audit_trace.py`: `D9D4145A81588CBF66D4A41AEE814198EB0B23E301EE2B3912A16D51C0744188`

## Stop rule

One independent auditor invocation. Any archive/member/hash/decode error is a terminal audit STOP; do not repair the auditor and reuse this audit attempt. No source runner, workflow, allocation, or old result may be changed.
