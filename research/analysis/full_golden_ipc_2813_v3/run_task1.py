"""Run only task-1 through the frozen historical route source, once."""
from __future__ import annotations
import argparse, json, os, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESEARCH = ROOT / "research" / "live_control"
HISTORICAL = ROOT / "research" / "analysis" / "full_golden_ipc_2705_v2" / "historical_route_source"
sys.path.insert(0, str(HISTORICAL)); sys.path.insert(1, str(RESEARCH))

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--out", type=Path, required=True); parser.add_argument("--seed", type=int, default=991035)
    args = parser.parse_args(); out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    import golden_desktop_demo as demo
    import integrated_efficiency_model_v1 as model
    import schema_preflight_v1 as preflight
    import run_integrated_efficiency_live_v1 as implementation
    chromium = Path(os.environ.get("AGENT_INTERFACE_CHROMIUM", ""))
    if not chromium.is_file(): chromium = Path(shutil.which("chromium") or shutil.which("chromium-browser") or "")
    if not chromium.is_file(): raise RuntimeError("Chromium is unavailable in the container")
    python = Path(sys.executable)
    config = {"windows_python": python, "windows_node": Path("/usr/bin/node"), "windows_cli": Path("/usr/bin/true"), "chromium": chromium}
    demo.windows_arg = lambda path: str(path)
    implementation, client_type = demo.configure_research_modules(config, chromium)
    model.windows_path = lambda path: str(Path(path).resolve()); preflight.windows_path = lambda path: str(Path(path).resolve())
    preflight.version = lambda _command: "container-host-ipc-v1"
    model.WINDOWS_PYTHON = python; preflight.WINDOWS_PYTHON = python; implementation.OUT = out; implementation.RuntimeClient = client_type
    (out / "doctor.json").write_text(json.dumps({"schema":"task1-route-doctor-v1","authority_granted":False,"task_limit":1,"chromium":str(chromium),"route_source":"historical_route_source"})+"\n", encoding="utf-8")
    preflight_result = implementation.preflight_call("persistent", "compiled")
    rows=[]; details=[]; workspace = out / "workspaces" / "persistent"
    with client_type(out / "arms" / "persistent", args.seed) as client:
        task = client.ready["goal"]["tasks"][0]
        row, cached, detail = implementation.run_task(client, "persistent", task, 0, None, workspace, out / "model-calls" / "persistent")
        rows.append(row); details.append(detail); independent = client.finish("finish-task1-route-2813-v3")
    report={"schema":"task1_route_successor_result_v1","issue":2813,"successor":"full_golden_ipc_2813_v3","status":"PASS_TASK1_EFFECT" if row["exact_submission"] and row["releases_verified"] and independent.get("success") is True else "HOLD_TASK1_EFFECT_NOT_REACHED","authority_granted":False,"preflight":preflight_result,"tasks":rows,"independent_evaluation":independent,"task_limit":1}
    (out / "report.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"status":report["status"],"exact_submission":row["exact_submission"],"releases_verified":row["releases_verified"]}, indent=2))
    return 0 if report["status"] == "PASS_TASK1_EFFECT" else 1

if __name__ == "__main__": raise SystemExit(main())
