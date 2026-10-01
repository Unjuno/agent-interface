# Host tool discovery and retained-image presentation recheck

The active primary tool inventory now exposes both agent_interface_integration
and agent_interface_native_research, each with native_start/status/observe/
submit/resume. This supersedes the historical unavailable-tool observation in
research/live_control/native_host_registration_v1 for this current host session.
It does not establish when or why host discovery changed.

Both directly called native_status tools returned needs_review: their configured
allocation directories already exist, with restart_allowed=false. Integration
points at this worktree's results-local/native-host-integration-01/run (Calc,
seed991221); native_research points at the separate admission-audit worktree's
native-host-direct-01/run (Calc, seed991125). Neither was started or replayed.

The primary then directly called agent_interface_integration.native_observe
with explicit stage4, selected after inspecting the retained source filenames.
The tool returned a native ImageContent and the attached observe-metadata.json.
The image was forwarded directly to the primary with image(block), without a
shell/SDK helper or view_image call. The primary saw Calc cells A1=587/A2=621.
The response identifies historical source sequence11, with image SHA256
ded136e479708a097a681831e14bf630892de650f05992969c8fb0bb72e6e37a.
No new capture or input occurred. This is retained-image presentation, not a
fresh GUI task, new saved-effect validation, or permission to act on old pixels.

The existing native_submit discovery still has the old expected_title wording
in this host inventory, whereas the fresh SDK trial saw the updated exact-title
description. Host tool publication can therefore reflect a different loaded
schema from the currently edited checkout; no automatic reload is established.

The next integration boundary is attaching a deliberately fresh allocation
through the available host entry point, with clear ownership and explicit
finish. Do not solve the consumed-path refusal by removing old evidence or
restarting that allocation. Neither desktop/Docker restart nor configuration
change was performed here. No latency/token improvement is measured.
