import asyncio, base64, ctypes, hashlib, json, re, subprocess, sys, time, uuid
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
from runtime.cli_v1.mcp_server import create_server

TARGET_NAME = "calculator"
TARGET_HWND = 55117672
TARGET_PID = 35132
EXPECTED_DISPLAY = "1042"
EXPECTED_RESULT = "1043"

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
def response_text(reply, label):
    texts = []
    images = 0
    for block in reply.content:
        if getattr(block, "type", None) == "text":
            texts.append(block.text)
        elif getattr(block, "type", None) == "image":
            name = f"observe-image-{images:02d}.png"
            (PACKET / "run" / name).write_bytes(base64.b64decode(block.data))
            images += 1
    (PACKET / "run" / f"{label}-raw.txt").write_text("\n".join(texts), encoding="utf-8")
    if not texts:
        raise RuntimeError(label + " returned no text block")
    try:
        return json.loads(texts[0])
    except json.JSONDecodeError as exc:
        raise RuntimeError(label + " returned invalid JSON: " + repr(exc)) from exc

def find_values(value, key):
    found = []
    if isinstance(value, dict):
        if key in value:
            found.append(value[key])
        for child in value.values():
            found.extend(find_values(child, key))
    elif isinstance(value, list):
        for child in value:
            found.extend(find_values(child, key))
    return found

def read_window_state():
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetAncestor.restype = wintypes.HWND
    def handle(value): return int(ctypes.cast(value, ctypes.c_void_p).value or 0)
    def pid(hwnd):
        process_id = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        return int(process_id.value)
    foreground = handle(user32.GetForegroundWindow())
    root = handle(user32.GetAncestor(foreground, 2)) if foreground else 0
    return {"target_hwnd": TARGET_HWND,
        "target_is_window": bool(user32.IsWindow(TARGET_HWND)),
        "target_visible": bool(user32.IsWindowVisible(TARGET_HWND)),
        "target_pid": pid(TARGET_HWND) if user32.IsWindow(TARGET_HWND) else None,
        "foreground_hwnd": foreground,
        "foreground_pid": pid(foreground) if foreground else None,
        "foreground_root_hwnd": root,
        "target_is_foreground_root": root == TARGET_HWND}

def read_client_rect():
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
    user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
    user32.GetClientRect.restype = wintypes.BOOL
    rect = RECT()
    if not user32.GetClientRect(TARGET_HWND, ctypes.byref(rect)):
        raise OSError(ctypes.get_last_error(), "GetClientRect failed")
    return [int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)]

def read_uia(expected="", timeout_ms=0):
    command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(PACKET / "uia_read.ps1"), "-Hwnd", str(TARGET_HWND),
        "-ExpectedDisplay", expected, "-TimeoutMs", str(timeout_ms)]
    started = time.perf_counter_ns()
    completed = subprocess.run(command, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=max(10, timeout_ms / 1000 + 5))
    ended = time.perf_counter_ns()
    raw = {"returncode": completed.returncode, "stdout": completed.stdout,
        "stderr": completed.stderr, "started_monotonic_ns": started,
        "ended_monotonic_ns": ended, "argv": command}
    if completed.returncode != 0:
        raise RuntimeError("UIA read failed: " + json.dumps(raw, ensure_ascii=False))
    try:
        value = json.loads(completed.stdout.strip())
    except json.JSONDecodeError as exc:
        raise RuntimeError("UIA output decode failed: " + json.dumps(raw, ensure_ascii=False)) from exc
    raw["parsed"] = value
    return raw

async def main():
    run = PACKET / "run"
    run.mkdir(exist_ok=True)
    baseline = read_uia()
    write_json(run / "uia-baseline.json", baseline)
    state_before = read_window_state()
    write_json(run / "win32-preflight.json", state_before)
    client_rect = read_client_rect()
    write_json(run / "win32-client-rect.json", {
        "rect": client_rect, "size": [client_rect[2] - client_rect[0], client_rect[3] - client_rect[1]]})
    if client_rect != [0, 0, 320, 533]:
        raise RuntimeError("STOPPED_BEFORE_OBSERVE: client bounds differ from frozen capture region")
    if baseline["parsed"]["display_digits"] != EXPECTED_DISPLAY:
        raise RuntimeError("STOPPED_BEFORE_OBSERVE: Calculator baseline changed")
    if not state_before["target_is_window"] or not state_before["target_visible"]:
        raise RuntimeError("STOPPED_BEFORE_OBSERVE: target unavailable or hidden")
    if state_before["target_pid"] != TARGET_PID or not state_before["target_is_foreground_root"]:
        raise RuntimeError("STOPPED_BEFORE_OBSERVE: target owner/focus changed")

    oracle_receipts = []
    def oracle(action):
        start = time.perf_counter_ns()
        result = read_uia(expected=EXPECTED_RESULT, timeout_ms=1500)
        end = time.perf_counter_ns()
        observed = result["parsed"]
        receipt = {"call_id": action["call_id"],
            "operation_id": action["operation_id"],
            "target_generation": action["target_generation"],
            "oracle_id": uuid.uuid4().hex,
            "outcome": "success" if observed["display_digits"] == EXPECTED_RESULT else "failure",
            "observed_monotonic_ns": end,
            "evidence_ref": "R15 UIA CalculatorResults exact display read",
            "oracle_start_monotonic_ns": start,
            "oracle_end_monotonic_ns": end,
            "uia": observed}
        oracle_receipts.append(receipt)
        return receipt

    server = create_server({TARGET_NAME: TARGET_HWND}, str(run / "server"),
        session_mode="supervised-win32", supervised_win32_task_oracle=oracle)
    dispatch_result = None
    call_id = None
    close_result = None
    try:
        observe_reply = await server.call_tool("interface_observe", {
            "target": TARGET_NAME, "frame": "window_client", "region": [0, 0, 320, 533],
            "compact": False, "report_refs": False})
        observation = response_text(observe_reply, "observation")
        write_json(run / "observation-parsed.json", observation)
        generations = sorted({value for value in find_values(observation, "target_generation")
            if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)})
        if len(generations) != 1:
            raise RuntimeError("STOPPED_BEFORE_INPUT: public observation lacks one matched generation")
        generation = generations[0]
        observation_ids = sorted({value for value in find_values(observation, "observation_id")
            if isinstance(value, str) and value})
        state_after_observe = read_window_state()
        baseline_after_observe = read_uia()
        write_json(run / "win32-after-observe.json", state_after_observe)
        write_json(run / "uia-after-observe.json", baseline_after_observe)
        if baseline_after_observe["parsed"]["display_digits"] != EXPECTED_DISPLAY:
            raise RuntimeError("STOPPED_BEFORE_INPUT: Calculator value changed after observation")
        if state_after_observe["target_pid"] != TARGET_PID or not state_after_observe["target_is_foreground_root"]:
            raise RuntimeError("STOPPED_BEFORE_INPUT: target owner/focus changed after observation")
        frozen = {"schema": "win32-standard-calculator-r15-frozen-target-v1",
            "attempt_id": "win32-standard-calculator-task-20261024-r15-6dd1e43e",
            "frozen_utc": datetime.now(timezone.utc).isoformat(),
            "source_commit": "21f53e7ed7ce200fe4959a858b59160f81569e21",
            "source_tree": "8356510627ae897467ce57317708f99b74a8c2d2",
            "backend_sha256": "87516d863db92c8a6e3202dfbf7d03063c942f19d8082b5142c128ffaf201b6c",
            "runner_sha256": digest(PACKET / "run_standard_calculator.py"),
            "uia_oracle_sha256": digest(PACKET / "uia_read.ps1"),
            "target": TARGET_NAME, "target_hwnd": TARGET_HWND, "target_pid": TARGET_PID,
            "target_generation": generation, "observation_ids": observation_ids,
            "baseline_display": baseline_after_observe["parsed"]["display_digits"],
            "expected_display": EXPECTED_RESULT,
            "program": {"ops": [{"op": "focus", "target": TARGET_NAME},
                {"op": "text", "text": "+1="}, {"op": "release_all"}],
                "source": {"observation_seq": 1, "binding_revision": 1,
                    "target_generations": {TARGET_NAME: generation}},
                "terminal": {"release_all_required": True}},
            "stop_rule": "One dispatch only; no replay. If it remains pending after 10s, one exact-call cancel, then read-only polling for at most 4s."}
        write_json(run / "FROZEN_TARGET.json", frozen)

        program = {"schema": "agent-interface/program-v1",
            "program_id": "calculator-plus-one-r15",
            "source": frozen["program"]["source"],
            "authority": {"lease_id": "r15-calculator-one-shot",
                "expires_at_ns": time.monotonic_ns() + 10_000_000_000},
            "terminal": frozen["program"]["terminal"],
            "ops": frozen["program"]["ops"]}
        dispatch_started = time.perf_counter_ns()
        reply = await server.call_tool("interface_dispatch", {
            "program": program, "current_observation_seq": 1,
            "current_binding_revision": 1, "wait_for_result_ms": 10000})
        dispatch_ended = time.perf_counter_ns()
        dispatch_result = response_text(reply, "dispatch")
        write_json(run / "dispatch-timing.json", {
            "start_monotonic_ns": dispatch_started,
            "end_monotonic_ns": dispatch_ended,
            "elapsed_ns": dispatch_ended - dispatch_started})
        call_id = dispatch_result.get("call_id")
        if not call_id:
            raise RuntimeError("dispatch returned no exact call ID")
        if dispatch_result.get("status") == "pending":
            cancel_reply = await server.call_tool("interface_cancel", {"call_id": call_id})
            cancel_result = response_text(cancel_reply, "cancel")
            write_json(run / "cancel.json", cancel_result)
            deadline = time.monotonic() + 4
            while time.monotonic() < deadline:
                result_reply = await server.call_tool("interface_results", {"call_id": call_id})
                retained = response_text(result_reply, "retained-results")
                write_json(run / "retained-results.json", retained)
                action = retained.get("action") or retained.get("supervision", {}).get("action") or {}
                if action.get("status") not in ("running", "cancel_pending"):
                    break
                await asyncio.sleep(0.05)
        if dispatch_result.get("status") == "returned":
            verify_reply = await server.call_tool("interface_verify_task", {
                "call_id": call_id, "wait_for_result_ms": 5000})
            verified = response_text(verify_reply, "task-verification")
            write_json(run / "task-verification.json", verified)
        if oracle_receipts:
            write_json(run / "oracle-receipts.json", oracle_receipts)
        if call_id:
            retained_reply = await server.call_tool("interface_results", {"call_id": call_id})
            retained = response_text(retained_reply, "final-results")
            write_json(run / "final-results.json", retained)
        post_uia = read_uia()
        write_json(run / "uia-post.json", post_uia)
        state_after = read_window_state()
        write_json(run / "win32-post.json", state_after)
    finally:
        try:
            close_reply = await server.call_tool("interface_close", {})
            close_result = response_text(close_reply, "close")
            write_json(run / "close.json", close_result)
        except BaseException as error:
            write_json(run / "close-error.json", {"error": repr(error)})

    verify = json.loads((run / "task-verification.json").read_text(encoding="utf-8")) if (run / "task-verification.json").exists() else {}
    post = json.loads((run / "uia-post.json").read_text(encoding="utf-8")) if (run / "uia-post.json").exists() else {}
    print(json.dumps({"attempt_id": "win32-standard-calculator-task-20261024-r15-6dd1e43e",
        "dispatch_status": (dispatch_result or {}).get("status"),
        "call_id": call_id, "task_success": verify.get("task_success"),
        "oracle_status": verify.get("status"),
        "post_display": post.get("parsed", {}).get("display_digits"),
        "release_confirmed": (dispatch_result or {}).get("release_confirmed"),
        "input_dispatched": (dispatch_result or {}).get("input_dispatched"),
        "target_generation": (dispatch_result or {}).get("target_generation"),
        "close_status": (close_result or {}).get("status")}, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except BaseException as error:
        (PACKET / "run" / "runner-error.json").write_text(
            json.dumps({"error_type": type(error).__name__, "error": str(error)},
                ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise
