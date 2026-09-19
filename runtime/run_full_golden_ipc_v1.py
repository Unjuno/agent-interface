"""Run the persistent golden six-task arm in Docker through host-model IPC."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=991029)
    args = parser.parse_args(); root = Path(__file__).resolve().parents[1]
    research = root / "research" / "live_control"
    sys.path.insert(0, str(research))
    import golden_desktop_demo as demo
    import integrated_efficiency_model_v1 as model
    import schema_preflight_v1 as preflight
    import run_integrated_efficiency_live_v1 as implementation

    python = Path(sys.executable); chromium = Path(os.environ.get("AGENT_INTERFACE_CHROMIUM", ""))
    if not chromium.is_file():
        chromium = Path(shutil.which("chromium") or shutil.which("chromium-browser") or "")
    if not chromium.is_file():
        raise RuntimeError("Chromium is unavailable in the Docker image")
    config = {"windows_python": python, "windows_node": Path("/usr/bin/node"),
              "windows_cli": Path("/usr/bin/true"), "chromium": chromium}
    demo.windows_arg = lambda path: str(path)
    implementation, client_type = demo.configure_research_modules(config, chromium)
    model.windows_path = lambda path: str(Path(path).resolve())
    preflight.windows_path = lambda path: str(Path(path).resolve())
    # The Docker IPC route has no legacy Node/npm CLI. Keep preflight identity
    # explicit and deterministic; the actual model endpoint is the host broker.
    preflight.version = lambda _command: "container-host-ipc-v1"
    model.WINDOWS_PYTHON = python; preflight.WINDOWS_PYTHON = python
    implementation.OUT = args.out.resolve(); implementation.RuntimeClient = client_type
    args.out.mkdir(parents=True, exist_ok=False)
    health = {"schema": "docker-golden-ipc-health-v1", "platform": sys.platform,
              "chromium": str(chromium), "display": os.environ.get("DISPLAY"),
              "model_boundary": "container-host-shared-volume-ipc", "authority_granted": False}
    (args.out / "doctor.json").write_text(json.dumps(health, indent=2) + "\n")
    preflight_result = implementation.preflight_call("persistent", "compiled")
    rows, independent = implementation.run_arm("persistent", args.seed,
                                                args.out / "workspaces" / "persistent")
    report = {"schema": "agent_interface_docker_host_ipc_live_v1",
              "seed": args.seed, "preflight": preflight_result,
              "tasks": rows, "independent_evaluation": independent,
              "passed": independent.get("success") is True and len(rows) == 6 and
              all(row["exact_submission"] and row["releases_verified"] for row in rows),
              "authority_granted": False,
              "scope": "one fresh persistent six-task Docker allocation through host model IPC"}
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "tasks": len(rows),
                      "output": str(args.out)}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
