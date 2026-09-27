# Issue #2907 — public MCP stale refusal + Chromium local effect

## Result

Allocation \`public-mcp-dispatch-stale-effect-2907-docker-20260927-04\` ran once in local Docker Desktop, Linux/amd64, image \`sha256:b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09\`, with \`--network none\`. Runner disposition: \`PASS_PUBLIC_MCP_STALE_EFFECT_RELEASE_SCOPED\`.

- One public persistent-X11 stdio MCP session: \`f863b70b81b74608a2e663f2cdfd703d\`.
- Stale sequence-1 dispatch at current sequence 2: \`refused / STALE_OBSERVATION\`, backend emissions 0.
- Fresh sequence-2 dispatch: \`completed\`, 154 program emissions; release verified with empty keys and buttons.
- Independent X11 title receipt: Chromium window 6291459 displayed \`agent-mcp-effect-2907-20260927-04 - Chromium\`.
- Same session explicitly closed; close attempted release and verified no held keys/buttons.
- Six \`interface_results\` responses: all \`finished\`, all \`operation_invoked=false\`, each bound to its original call ID and the single stdio ClientSession context.
- Model/provider/network calls 0; authority false; no live MCP server or owned process; X socket absent.

## Independent audit history

The first separate offline Docker audit is retained unchanged as \`HOLD_RAW_AUDIT\`, errors=[], with one failed transport-split mutation control and an incomplete control set. Its SHA-256 is \`9caf0766acdaf4259edd8e7858c5e948b21baa9ee38c821d43f0cc407617ab5e\`.

A versioned auditor correction was construction-tested, published and read back before a fresh \`--network none --read-only\` Docker re-audit. Corrected audit: \`PASS_RAW_AUDIT\`, errors=[], 8/8 corruption controls rejected, including persisted-effect tampering, split transport, and retained call-ID mismatch. Audit SHA-256: \`abb385a5f5ec31c831b3111cdfa100aac86586c8c80308ea5ae106cd82e98691\`.

Raw result SHA-256: \`38125998c85525e925108fb66b6218953339d710b4d04c40ca494b282c773906\`  
Trace SHA-256: \`08bbfcbb8d474701cabbcf13a1b83b771fb03053185e38a34ec4a828fdb3bcf8\`  
Persisted effect receipt SHA-256: \`cec3a93cd1694c494df334c90b0f303c5d50a962fe1985689a985254e24dae9a\`

## Prior stops retained

Allocations 01, 02 and 03 are documented in their original paths and remain immutable. #01: caller schema STOP. #02: local raw showed scoped behavior but branch source did not match frozen source and original auditor held. #03: wrapper entrypoint STOP before MCP/input. They are not pooled with this allocation.

## Scope limit

This is one deterministic caller, one Chromium local-page effect, one stale-sequence negative, and one public persistent MCP session. It does not test production controller/lease issuance, Calc or Inkscape, the full #2907 focus/modal/geometry/window-replacement/return schedule, #2789 six-task acceptance, model-mediated task success, broad utility/performance/reliability, or product readiness. #2907 and #2789 remain open.

All formal and audit execution was local Docker. GitHub MCP was used to inspect and retain source/evidence; no workflow or Actions job was used.

