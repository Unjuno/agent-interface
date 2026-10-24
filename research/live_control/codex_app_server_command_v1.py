"""Capability-minimized Codex app-server command for planner-only sessions."""
import json
import os
from pathlib import Path
import re
import tomllib


DISABLED_FEATURES = (
    "apps", "plugins", "remote_plugin", "browser_use", "browser_use_external",
    "computer_use", "in_app_browser", "code_mode", "code_mode_host",
)


def configured_mcp_server_names(codex_home=None):
    """Read only MCP names from the selected Codex config; never its values."""
    if codex_home is None:
        configured_home = os.environ.get("CODEX_HOME")
        codex_home = configured_home if configured_home else Path.home() / ".codex"
    config_path = Path(codex_home) / "config.toml"
    if not config_path.is_file():
        return ()
    with config_path.open("rb") as stream:
        config = tomllib.load(stream)
    servers = config.get("mcp_servers", {})
    if not isinstance(servers, dict):
        raise ValueError("mcp_servers must be a table in Codex config")
    names = []
    for name in servers:
        if not isinstance(name, str) or not name:
            raise ValueError("Codex MCP server names must be nonempty strings")
        names.append(name)
    return tuple(sorted(names))


def _toml_key(name):
    if re.fullmatch(r"[A-Za-z0-9_-]+", name):
        return name
    return json.dumps(name, ensure_ascii=False)


def command(node, cli, *, codex_home=None):
    result = [str(node), str(cli), "app-server", "--stdio"]
    for feature in DISABLED_FEATURES:
        result += ["--disable", feature]
    # Only override entries that exist. Adding `mcp_servers.foo.enabled=false`
    # for an absent server creates an invalid partial server table in newer CLI
    # versions (which reject it as an invalid transport).
    for name in configured_mcp_server_names(codex_home):
        result += ["-c", f"mcp_servers.{_toml_key(name)}.enabled=false"]
    return result
