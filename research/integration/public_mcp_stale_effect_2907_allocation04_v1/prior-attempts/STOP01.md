# Allocation 01 — caller-management response schema STOP

Allocation `public-mcp-dispatch-stale-effect-2907-docker-20260927-01` was formally invoked once in local Docker Desktop, Linux/amd64, with `--network none`. It is consumed and immutable.

## First result

Runner disposition preserved verbatim: `STOP_OR_FAIL_CALLER`; caught error was `PUBLIC_RECEIPT_SCHEMA_MISMATCH`. The first five responses were public `review-v1` / `receipt-view-v1` envelopes. The sixth call, `interface_close`, returned a flat management report (no `review-v1` or receipt-view wrapper). The adapter rejected that valid second response shape. It stopped before issuing any `interface_results` retained reads and before serializing the measured WM title/effect receipt. Do not reinterpret its missing effect record as success or as app failure.

Formal result SHA-256: `f5dc5868ecf5cfef09e683a17be3ceba91eb82f07847ed15fa2769e15813b028`  
Fresh dispatch response SHA-256: `b1b0e6bc520693eedd600d4a3072f9de9f423c906d5bc0b5e41574f77972af`  
Flat close response SHA-256: `bd600e74e950618adcc324ee80f24d0def270296230539097530e0b41d62083b`

## Offline raw-only reconstruction

A separate `--network none --read-only` Docker audit read the exact response files, decoded all six outer content envelopes, bound three observation PNGs to their separately saved bytes, and reconstructed one session ID throughout:

- Old observation sequence: `refused / STALE_OBSERVATION`, backend emissions 0.
- Fresh public MCP dispatch: `completed`, 154 program emissions; the release receipt verified empty keys and buttons.
- Post-action observation returned in the same session.
- Flat `interface_close` report: closed, release attempted, connection-close attempted.
- No live MCP server process or X socket remained.
- Five frozen corruption controls rejected.

Audit: `PASS_RAW_STOP_AUDIT`, errors=[]; audit JSON SHA-256 `abe9028bd4840417c25900752109e71c1ccfef3a0bb48bb9aa38c51ae5fd32ae`.

Disposition is still `STOP_CALLER_MANAGEMENT_SCHEMA_EFFECT_AND_RETAINED_READBACK_UNVERIFIED`. The runner had observed a title-marker match before close, but failed to persist that oracle; screenshot crop is only the browser toolbar and cannot prove the page effect. Therefore effect verification and all six retained-result readbacks remain unverified. This is not a full PASS or FAIL of the public action contract.

## Scope

Local Docker only; zero model/network. No MCP call, input, or mutation occurred during the offline audit. Formal source, complete raw MCP/server records, process/environment output, original first disposition, independent stop-audit code and audit output are retained under `formal01/` and `audit01/`. A separate successor allocation with a decoder for both documented response shapes is required for a fresh attempt; this allocation is never resumed or replayed.


