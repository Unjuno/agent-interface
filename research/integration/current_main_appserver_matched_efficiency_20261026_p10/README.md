# P10 — matched App Server caller routes

This packet compares one direct public-input route with one compiled public-caller route on the same deterministic synthetic Fake X task. It is a small exploratory efficiency sample, not a live GUI, MAP01, WSLc, blocked-I/O, or reliability qualification.

## Frozen trial plan

See `PREREGISTRATION.md`, `CONDITIONS.json`, `RUN-ORDER.txt`, and `PRELAUNCH.json`. Run six one-shot cells in the listed order. Each starts a fresh caller/session and makes one model generation. Do not retry, replace, reorder, or reinterpret a failed/unknown first outcome. The model/effort are `gpt-6.1-sol`/`low`. The provider is the installed Codex App Server, and the task is to identify and click the green target from the exact screenshot returned by the public observation tool.

## Local execution

Use a fresh private raw root outside the repository and a fresh neutral workspace root. The run refuses to overwrite an existing cell directory.

```powershell
$env:AGENT_INTERFACE_P10_RAW_ROOT = 'C:\Users\user\AppData\Local\agent-interface-research\current_main_appserver_matched_efficiency_20261026_p10'
$env:AGENT_INTERFACE_P10_WORKSPACE_ROOT = 'C:\AgentInterfaceP10-20261026-p10-5e6a9d3b'
py -3.13 -m research.integration.current_main_appserver_matched_efficiency_20261026_p10.run_arm --pair p01 --arm direct_public_input
```

Run the remaining cells exactly as listed in `RUN-ORDER.txt`. If execution starts and ends without a valid result, retain that outcome and proceed to the next preregistered cell only after confirming the previous App Server and synthetic owner are closed. No WSLc, Docker, physical input, or GZDoom is used by this packet.

## Custody and privacy

The private raw root is the source of truth. Keep it local and immutable. The per-cell `RAW-SHA256.json` records byte counts and hashes for every cell file except itself. Run the private auditor against that root before exporting anything. `export_p10.py` omits `ledger/raw/**` and `.bin` files from the public copy, includes their relative-path/size/SHA index, and redacts paths and identifiers in the copied text/JSON files. It never edits the private raw files. Because raw bytes are withheld from the repository, a public reader can verify the published hash index but cannot independently reconstruct provider-attempt raw reconciliation.

## Interpretation

`audit_p10.py` reports each cell and paired direct-minus-compiled differences for provider-reported token counts, provider-turn duration, observation-to-action-return latency, and total trial duration. It also checks exact independent effect and verified release, App Server usage against the terminal result, attempt-recorder raw reconciliation, and each private raw manifest. It does not claim independent upstream billing/account-level usage: Codex App Server and its journal are the available accounting source. Three pairs are descriptive only; report successes separately from timing and token differences.
