"""One request-specific OrbStack model container over one host IPC directory."""
from __future__ import annotations
import hashlib, json, os, shutil, subprocess, time
from pathlib import Path

ROOT = Path(os.environ["ISSUE3824_OUT"]).resolve()
MIRROR_ROOT = ROOT / "broker-mirrors"
IPC_ROOT = ROOT / "ipc"
RUNNER = Path(os.environ["ISSUE3824_RUNNER"]).resolve()
IMAGE = os.environ["ISSUE3824_MODEL_IMAGE"]
CONTAINER_IMAGE = os.environ["ISSUE3824_RUNNER_IMAGE"]
CODEX = os.environ["ISSUE3824_CODEX_EXE"]
REQUEST_COUNT = 0

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def prepare_request(contract, prompt, image=None):
    IPC_ROOT.mkdir(parents=True, exist_ok=True)
    index = len(list(IPC_ROOT.glob("request-*"))) + 1
    request = ROOT / "requests" / f"request-{index:02d}"
    mirror = MIRROR_ROOT / f"request-{index:02d}"
    ipc = IPC_ROOT / f"request-{index:02d}"
    workspace = mirror / "workspace"
    for path in (request, mirror, ipc, workspace): path.mkdir(parents=True, exist_ok=False)
    source_dir = Path(__file__).resolve().parent
    schema_name = "plain_form_points_schema_v1.json" if contract == "plain" else "compiled_form_grounding_schema_v1.json"
    preflight = image is None
    instruction_name = ("schema_preflight_responder_v1.txt" if preflight else
                        "plain_form_points_responder_v1.txt" if contract == "plain" else
                        "compiled_form_grounding_responder_v1.txt")
    live = Path(os.environ["ISSUE3824_LIVE_SOURCE"])
    schema = live / schema_name; instructions = live / instruction_name
    shutil.copyfile(schema, mirror / "schema.json")
    shutil.copyfile(instructions, mirror / "instructions.txt")
    if image is not None:
        shutil.copyfile(image, mirror / "image.png")
        if sha(image) != sha(mirror / "image.png"): raise RuntimeError("image mirror hash mismatch")
    return request, mirror, ipc, workspace, schema, instructions

def call(root: Path, prompt: str, image: Path, contract: str, workspace: Path):
    global REQUEST_COUNT
    REQUEST_COUNT += 1
    if REQUEST_COUNT > 17: raise RuntimeError("STOP_17_CALL_LIMIT_BEFORE_REQUEST")
    Path(root).mkdir(parents=True, exist_ok=False)
    request, mirror, ipc, work, schema, instructions = prepare_request(contract, prompt, image)
    prompt_path = request / "prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8", newline="\n")
    output = request / "container-output"
    command = ["docker", "run", "--rm", "--network", "none", "-e", "HOST_MODEL_IPC_DIR=/ipc",
        "-v", f"{output}:/out", "-v", f"{ipc}:/ipc", "-v", f"{RUNNER}:/repo/runner.py:ro",
        "-v", f"{instructions}:/repo/instructions.txt:ro", "-v", f"{prompt_path}:/repo/prompt.txt:ro",
        "-v", f"{schema}:/repo/schema.json:ro", "-v", f"{work}:/repo/workspace"]
    if image is not None:
        command += ["-v", f"{image}:/repo/image.png:ro"]
    command += [CONTAINER_IMAGE, "python", "/repo/runner.py", "/usr/bin/node", "/usr/bin/true",
        "/repo/prompt.txt", "/repo/workspace", "/out/run",
        "handle" if image is None else "coordinate", "-" if image is None else "/repo/image.png",
        "/repo/instructions.txt", "/repo/schema.json"]
    started = time.time_ns()
    (request / "invocation.json").write_text(json.dumps({"command": command,
        "mode": "handle" if image is None else "coordinate", "contract": contract,
        "image_sha256": None if image is None else sha(image), "retry": False,
        "authority_granted": False, "started_ns": started}, indent=2)+"\n")
    (request / "workspace-ref").write_text(str(work)+"\n")
    env = os.environ.copy(); env["HOST_MODEL_IPC_DIR"] = str(ipc)
    env["ISSUE3824_BROKER_REPO"] = str(mirror)
    completed = subprocess.run(command, env=env, capture_output=True, text=True, timeout=180)
    (request / "container.stdout.txt").write_text(completed.stdout)
    (request / "container.stderr.txt").write_text(completed.stderr)
    if completed.returncode != 0: raise RuntimeError("STOP_MODEL_CONTAINER:"+str(completed.returncode))
    from runtime.docker_schema_preflight_v1 import validate_model_response
    validation = validate_model_response(output / "run/events.jsonl", schema)
    (request / "schema-validation.json").write_text(json.dumps(validation, indent=2)+"\n")
    if validation.get("status") != "PASS": raise RuntimeError("STOP_MODEL_SCHEMA:"+str(validation.get("status")))
    if image is None:
        from preflight_response_v1 import parse_schema_preflight
        result = parse_schema_preflight(output / "run/events.jsonl",
            output / "run/process.json", schema)
    else:
        import integrated_efficiency_model_v1 as model
        result = model.parse(output / "run", contract)
    result["image_sha256"] = None if image is None else sha(image)
    result["request_directory"] = str(request)
    (request / "result.json").write_text(json.dumps(result, indent=2)+"\n")
    return result
