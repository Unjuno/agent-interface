# Current-main actual App Server to public MCP smoke on Fake X

**Status: partial pass / HOLD for the integrated live-control and efficiency goal.** Source was current main `5d9a4e9d3160307f845835ead5b1a337e486f40d`. The five append-only packets preserve every setup failure and the one successful provider-to-caller run. No packet used WSLc or physical desktop input.

## Trial dispositions

| Packet | First outcome | Model turn / caller input | Disposition |
|---|---|---|---|
| [p01](current_main_appserver_public_mcp_fake_x_20261025_p01/PREREGISTRATION.md) | Script import failed (`runtime` not on `sys.path`) | None | Preserved; not rerun |
| [p02](current_main_appserver_public_mcp_fake_x_20261025_p02/PREREGISTRATION.md) | Harness pre-created an exclusive App Server journal | None | Preserved; not rerun |
| [p03](current_main_appserver_public_mcp_fake_x_20261025_p03/PREREGISTRATION.md) | Launcher added absent MCP names, and current Codex CLI rejected `mcp_servers.blender` as invalid transport | Initialize process only; no model turn | Preserved; not rerun. A bounded initialize-only diagnostic succeeded when disabling only configured MCP names |
| [p04](current_main_appserver_public_mcp_fake_x_20261025_p04/PREREGISTRATION.md) | Provider rejected incomplete object schema with HTTP 400 `invalid_json_schema` | `turn/start` submitted; no token usage and no public compiled dispatch | Preserved; not rerun |
| [p05](current_main_appserver_public_mcp_fake_x_20261025_p05/PREREGISTRATION.md) | `PASS_PROVIDER_CALLER_FAKE_X_ONLY` | One real App Server turn; one `interface_guarded_compiled` dispatch | Passed its preregistered synthetic integration gate |

## p05 evidence

The App Server returned one completed `gpt-6.1-sol` / low turn. Reported usage was 11,090 input tokens, 410 output tokens, 65 reasoning tokens, zero cached-input and cache-write-input tokens. Image-input usage was absent, so detailed usage and billing remain incomplete. The attempt recorder reconciled one model attempt and three public MCP calls (initial observation, target mint, compiled execution); its ledger is complete. The retained protocol journal has one matching turn usage update, and the adapter checked returned usage against that journal slice.

The public caller returned a local method outcome of `TASK_SUCCEEDED`; its action receipt marked release verified. The runtime result correctly left `task_success` null. An independent synthetic Fake X readback found pixel `(1,1) == RGB (255,0,0)` and recorded the task-score certificate as true. End-to-end elapsed time from initial observation through score was 12.510 seconds. The run manifest's 79 file hashes match, and 54 retained JSON files parse. Before publication, host and installation identifiers in the p04/p05 protocol traces and the p05 session authorization fields were redacted; [redaction records](current_main_appserver_public_mcp_fake_x_20261025_p05/REDACTIONS.json) preserve original and sanitized hashes without retaining those values in the public packet. See [the independent audit](current_main_appserver_public_mcp_fake_x_20261025_p05/AUDIT.json) and [p05 README](current_main_appserver_public_mcp_fake_x_20261025_p05/README.md).

The prompt contained the exact prevalidated one-step payload. This tests actual provider usage and standard-caller wiring, not visual target selection or model grounding. The application and oracle were synthetic; no physical release, blocked-platform-I/O recovery, live application, MAP01, WSLc, baseline comparison, cold/warm/repair economics, or reliability estimate is established. The retained App Server protocol is not an independent upstream provider log, and image-input token details are unavailable. Keep Issue #57 at HOLD for the required live task and matched efficiency report.