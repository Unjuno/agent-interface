# Fresh allocation connection prepared, not applied to the active host

## Configuration follow-up (2026-09-27)

The preparation account below is historical. The user subsequently authorized
configuration, and the global `agent-interface-integration` registration was
saved. A fresh `codex mcp get agent-interface-integration --json` confirms it is
enabled, starts the WSL command for Inkscape allocation
`results-local/native-host-integration-02`, seed 991284, and uses startup/tool
timeouts of 30/45 seconds. Re-editing the registration is not the next step.

The active host's `native_status` still returns the consumed Calc allocation
`native-host-integration-01/run`, seed 991221, `needs_review`, with restart
disallowed. Saving configuration has therefore not refreshed this connection.
An attempted app UI refresh did not establish a successful server reload.
No fresh direct-host run or performance result is claimed. After host reload,
verify the allocation, app, seed and `not_started` state before starting.

## Historical preparation account

The next-session directory retains a Windows-SDK-to-WSL handshake for a fresh
native-host-integration-02 Inkscape allocation (seed991284, max8 stages,
text gap2ms, system Python harness). It initialized, listed tools and called
native_status only. The result was not_started, the allocation directory did
not exist afterward, and the schema contained the new exact-title wording.
No GUI/input, host configuration write, Docker restart or previous-run deletion
occurred. handshake.py records the original results-local helper; its relative
repository discovery assumes that original location, not this copied archive.

The active host still exposes the consumed integration allocation. Local CLI
`codex mcp get agent-interface-integration --json` reports no such server. The
parent project's .codex/config.toml instead contains native-research aimed at a
different checkout. CLI get for that name also currently reports not found;
its historical effective-layer success is not current proof of visibility.
No unrelated server, trust entry or global setting was changed as a guess.

The installed CLI's mcp help lists list/get/add/remove/login/logout/help, with
no reload command. The active tool inventory has no host MCP configuration or
restart tool. Official MCP documentation describes app settings and a Restart
step: https://learn.chatgpt.com/docs/extend/mcp?surface=cli
This does not prove a CLI-created app-server can reload the existing host.

The user was asked to apply the prepared command/args to the existing integration
entry and restart that server, or choose continued SDK use. Configuration is
ready and reviewable; no reply, host reload or fresh direct run is claimed.
When the host is updated, call native_status first and check the run directory,
app and seed. Only the explicitly fresh not_started allocation may be started.
Do not retry or relaunch the old consumed allocation. Recheck tool descriptions;
a fresh process and refreshed host schema are separate observations.
