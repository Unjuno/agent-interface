"""Construct a no-tool Codex CLI invocation for a single frozen image case."""


DISABLED_FEATURES = (
    "shell_tool",
    "unified_exec_tty",
    "code_mode",
    "code_mode_host",
    "computer_use",
    "browser_use",
    "browser_use_external",
    "browser_use_full_cdp_access",
    "apps",
    "standalone_web_search",
    "sleep_tool",
    "tool_call_mcp_elicitation",
    "skill_mcp_dependency_install",
    "skill_search",
    "request_permissions_tool",
    "workspace_dependencies",
    "view_image",
    "shell_snapshot",
    "shell_snapshot_v2",
    "tool_suggest",
    "worktrees",
    "auth_elicitation",
    "collaboration_modes",
    "daemon_auto_start",
    "multi_agent",
    "plugins",
    "plugin_sharing",
    "remote_plugin",
    "hooks",
    "in_app_browser",
    "image_generation",
    "in_app_local_automation",
    "realtime_conversation",
)


def build_args(image, schema, model="gpt-6-astra"):
    if not model or not image or not schema:
        raise ValueError("model, image and schema are required")
    args = [
        "exec",
        "--ignore-user-config",
        "--ignore-rules",
        "--strict-config",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--model",
        model,
        "-c",
        'model_reasoning_effort="low"',
        "--image",
        str(image),
        "--output-schema",
        str(schema),
    ]
    for feature in DISABLED_FEATURES:
        args.extend(("--disable", feature))
    args.append("-")
    return args
