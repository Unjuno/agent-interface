"""Capability-minimized Codex app-server command for planner-only sessions."""


DISABLED_FEATURES = (
    "apps", "plugins", "remote_plugin", "browser_use", "browser_use_external",
    "computer_use", "in_app_browser", "code_mode", "code_mode_host",
)
DISABLED_MCPS = ("blender", "chrome-devtools", "node_repl", "playwright", "puppeteer")


def command(node, cli):
    result = [str(node), str(cli), "app-server", "--stdio"]
    for feature in DISABLED_FEATURES:
        result += ["--disable", feature]
    for name in DISABLED_MCPS:
        result += ["-c", f"mcp_servers.{name}.enabled=false"]
    return result
