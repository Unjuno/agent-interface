"""Fresh-start finite MAP01 runner with explicit host image-path mapping."""
from __future__ import annotations

import hashlib
from pathlib import Path
import shlex
import sys
import types

REPO = Path(__file__).resolve().parents[3]
DOOM = REPO / "research" / "doom"
SOURCE = DOOM / "map01_overlap_controller_v39.py"
IMAGE = "issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e"
WAD = Path("/tmp/issue2679-orbstack-preflight/freedoom2.wad")
CODEX = "/opt/homebrew/bin/codex"
DISABLED_MCPS = (
    "playwright", "chrome-devtools", "google-chrome", "huggingface",
    "node_repl", "computer-use",
)
SESSION_OUTPUT_FILTER = """import json,os,sys
host_root=os.environ["AGENT_RESULT_ROOT_HOST"]
for line in sys.stdin:
    row=json.loads(line)
    if row.get("event")=="observation":
        image=row.get("image")
        if isinstance(image,str) and image.startswith("/out/"):
            row["image"]=host_root+image[len("/out"):]
    if row.get("event")=="post_control_score":
        row={"event":"post_control_score","evaluator_score_withheld":True}
    print(json.dumps(row,separators=(",",":")),flush=True)
"""
REPLACEMENTS = (
    ('parser.add_argument("--load-fixture-manifest", type=Path, required=True)',
     'parser.add_argument("--load-fixture-manifest", type=Path, required=False)'),
    ('    if runtime_fixture is None:\n'
     '        raise RuntimeError("v28 requires a loaded fixture receipt")\n',
     '    # Fresh-start allocation: no save-state fixture is loaded.\n'),
)


def effective_source():
    text = SOURCE.read_text(encoding="utf-8")
    for old, new in REPLACEMENTS:
        if text.count(old) != 1:
            raise RuntimeError(f"expected one exact fresh-start anchor: {old!r}")
        text = text.replace(old, new, 1)
    return text


def load_controller():
    sys.path.insert(0, str(DOOM))
    sys.path.insert(0, str(REPO / "research" / "live_control"))
    source = effective_source()
    module = types.ModuleType("map01_overlap_controller_v39_freshstart_v3")
    module.__file__ = str(SOURCE)
    module.__package__ = ""
    exec(compile(source, str(SOURCE), "exec"), module.__dict__)

    def app_server_command():
        command = [CODEX, "app-server", "--stdio"]
        for feature in module.DISABLED_FEATURES:
            command += ["--disable", feature]
        command += ["-c", "mcp_servers={}"]
        for name in DISABLED_MCPS:
            command += ["-c", f"mcp_servers.{name}.enabled=false"]
        return command

    def session_command(args, runtime):
        output_root = Path(args.out).resolve()
        shell = (
            "mkdir -p /tmp/home /tmp/xdg-config /tmp/xdg-cache /tmp/xdg-runtime "
            "&& chmod 700 /tmp/xdg-runtime && "
            "python3 /src/research/doom/session_map01_v12.py "
            f"--out /out/runtime --seed {int(args.seed)} "
            "--timeout-seconds 600 --skill 1 | python3 -c "
            + shlex.quote(SESSION_OUTPUT_FILTER)
        )
        return [
            "docker", "run", "--rm", "-i", "--platform", "linux/arm64",
            "--network", "none", "--read-only", "--workdir", "/tmp",
            "--tmpfs", "/tmp:rw,nosuid,nodev,size=128m",
            "--tmpfs", "/run:rw,nosuid,nodev,size=32m",
            "-e", "PYTHONPATH=/src:/src/research/real_apps_v1",
            "-e", "HOME=/tmp/home", "-e", "XDG_CONFIG_HOME=/tmp/xdg-config",
            "-e", "XDG_CACHE_HOME=/tmp/xdg-cache",
            "-e", "XDG_RUNTIME_DIR=/tmp/xdg-runtime",
            "-e", f"AGENT_RESULT_ROOT_HOST={output_root}",
            "-v", f"{REPO}:/src:ro", "-v", f"{output_root}:/out",
            "--entrypoint", "/usr/bin/bash", IMAGE, "-o", "pipefail", "-c", shell,
        ]

    module.win = lambda path: str(Path(path).resolve())
    module.app_server_command = app_server_command
    module.session_command = session_command
    module.WAD = WAD
    module._freshstart_effective_source = source
    module._freshstart_sha256 = hashlib.sha256(source.encode("utf-8")).hexdigest()
    return module


def main():
    module = load_controller()
    if "--prepare-only" in sys.argv:
        target = Path(sys.argv[sys.argv.index("--prepare-only") + 1]).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(module._freshstart_effective_source, encoding="utf-8")
        print(f"effective_controller_sha256={module._freshstart_sha256}")
        print(f"effective_controller_path={target}")
        return
    module.main()


if __name__ == "__main__":
    main()
