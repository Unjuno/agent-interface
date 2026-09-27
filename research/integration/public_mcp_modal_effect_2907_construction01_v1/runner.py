"""One local-Docker public-MCP modal appearance/dismissal construction."""
import asyncio
import base64
import hashlib
import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

OUT = Path(os.environ.get("OUTPUT_DIR", "/out/construction01"))
DISPLAY = ":151"
IMAGE = os.environ["EXPERIMENT_IMAGE_ID"]
SOURCE_COMMIT = os.environ["SOURCE_COMMIT"]
RUNNER_SHA256 = os.environ["RUNNER_SHA256"]
ENV = dict(os.environ, DISPLAY=DISPLAY, HOME="/tmp/ai-home",
           XDG_CONFIG_HOME="/tmp/ai-config")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False).encode()
    path.write_bytes(data + b"\n")
    return hashlib.sha256(data + b"\n").hexdigest()


def run(argv, timeout=8):
    return subprocess.run(argv, env=ENV, text=True, capture_output=True,
                          check=False, timeout=timeout)


def proc_table():
    table = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "stat").read_text()
            fields = raw[raw.rfind(")") + 2:].split()
            table[int(entry.name)] = {"state": fields[0], "ppid": int(fields[1])}
        except (OSError, ValueError, IndexError):
            continue
    return table


def descendants(root):
    table = proc_table()
    found = {int(root)}
    changed = True
    while changed:
        changed = False
        for pid, row in table.items():
            if row["ppid"] in found and pid not in found:
                found.add(pid)
                changed = True
    return sorted(found)


def visible_windows():
    q = run(["xdotool", "search", "--onlyvisible", "--name", ".*"], timeout=5)
    return sorted({int(x) for x in q.stdout.splitlines() if x.strip().isdigit()})


def window_info(wid):
    p = run(["xprop", "-id", str(wid), "_NET_WM_PID", "WM_CLASS", "WM_NAME",
             "WM_TRANSIENT_FOR"], timeout=5)
    g = run(["xdotool", "getwindowgeometry", "--shell", str(wid)], timeout=5)
    owner = re.search(r"_NET_WM_PID\(CARDINAL\) = (\d+)", p.stdout)
    transient = re.search(r"WM_TRANSIENT_FOR\(WINDOW\): window id # (0x[0-9a-fA-F]+)", p.stdout)
    dims = {}
    for key in ("X", "Y", "WIDTH", "HEIGHT"):
        m = re.search(rf"^{key}=(\d+)$", g.stdout, flags=re.M)
        if m:
            dims[key] = int(m.group(1))
    title = run(["xdotool", "getwindowname", str(wid)], timeout=5).stdout.strip()
    return {"window_id": int(wid), "title": title,
            "owner_pid": int(owner.group(1)) if owner else None,
            "wm_class_raw": p.stdout, "transient_for": transient.group(1) if transient else None,
            "geometry": dims, "xprop_returncode": p.returncode,
            "geometry_returncode": g.returncode}


def snapshot():
    return [window_info(wid) for wid in visible_windows()]


def is_open_dialog(row):
    return row["title"].strip().lower() in {"open", "open file"}


def open_rows():
    return [row for row in snapshot() if is_open_dialog(row)]


def launch_calc():
    before = set(visible_windows())
    profile = "file:///tmp/ai-calc-profile"
    p = subprocess.Popen(["libreoffice", "--calc", "--norestore", "--nolockcheck",
                          "--nofirststartwizard", "--nodefault",
                          f"-env:UserInstallation={profile}"], env=ENV,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
    deadline = time.monotonic() + 45
    candidates = []
    while time.monotonic() < deadline:
        for wid in sorted(set(visible_windows()) - before):
            row = window_info(wid)
            if ("libreoffice-calc" in row["wm_class_raw"].lower() and
                    "libreoffice calc" in row["title"].lower() and
                    row["geometry"].get("WIDTH", 0) >= 600 and
                    row["geometry"].get("HEIGHT", 0) >= 400):
                return p, row
            candidates.append(row)
        time.sleep(.2)
    raise RuntimeError("CALC_MAIN_WINDOW_NOT_READY:" + json.dumps(candidates[-8:]))


def public_payload(result):
    texts = [item.text for item in result.content if getattr(item, "type", None) == "text"]
    if len(texts) != 1:
        raise RuntimeError("MCP_TEXT_RECEIPT_COUNT:" + str(len(texts)))
    return json.loads(texts[0])


def raw_result(payload):
    raw = payload.get("receipt", {}).get("source", {}).get("raw_report")
    if isinstance(raw, dict):
        return raw.get("result", raw.get("observation", raw))
    return payload.get("result", payload)


def save_response(path, result):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(result.model_dump(mode="json"), sort_keys=True,
                      indent=2, ensure_ascii=False).encode()
    path.write_bytes(data + b"\n")
    images = []
    for n, item in enumerate(result.content):
        if getattr(item, "type", None) == "image":
            image = base64.b64decode(item.data, validate=True)
            image_path = path.with_name(path.stem + f"-image{n}.png")
            image_path.write_bytes(image)
            images.append({"path": str(image_path.relative_to(OUT)),
                           "bytes": len(image),
                           "sha256": hashlib.sha256(image).hexdigest()})
    return hashlib.sha256(data + b"\n").hexdigest(), images


def program(program_id, seq, revision, chord):
    return {
        "schema": "agent-interface/program-v1",
        "program_id": program_id,
        "source": {"observation_seq": seq, "binding_revision": revision},
        "authority": {"lease_id": "local-construction-only",
                      "expires_at_ns": time.monotonic_ns() + 90_000_000_000},
        "terminal": {"release_all_required": True},
        "ops": [{"op": "focus", "target": "calc"},
                {"op": "key_chord", "keys": chord},
                {"op": "release_all"}],
    }


async def sequence(root_id):
    params = StdioServerParameters(
        command="python3",
        args=["-m", "runtime.cli_v1.mcp_server", "--targets", str(OUT / "targets.json"),
              "--output-directory", str(OUT / "server-receipts"), "--display", DISPLAY,
              "--session-mode", "persistent-x11"], env=ENV, cwd="/opt/importroot")
    tr = {"calls": [], "decision": "HOLD_INCOMPLETE", "root_window_id": root_id,
          "model_calls": 0, "network_calls": 0, "authority_granted": False}
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as client:
            await client.initialize()

            async def call(index, operation, args):
                result = await client.call_tool("interface_" + operation, args)
                path = OUT / "mcp" / f"{index:02d}-{operation}.json"
                response_sha, images = save_response(path, result)
                row = public_payload(result)
                call_row = {"index": index, "operation": operation,
                            "call_id": row.get("call_id"), "response_sha256": response_sha,
                            "images": images, "status": row.get("status"),
                            "session": row.get("session")}
                tr["calls"].append(call_row)
                tr[f"{index:02d}_{operation}"] = row
                write_json(OUT / "trace.partial.json", tr)
                return row

            close_done = False
            try:
                first = await call(1, "observe", {"target": "calc", "frame": "window_client",
                                  "region": [0, 0, 160, 120]})
                s1 = first.get("session", {})
                tr["session_id"] = s1.get("session_id")
                tr["revision_initial"] = s1.get("binding_revision")
                if first.get("status") != "returned" or s1.get("binding_revision") != 1:
                    raise RuntimeError("INITIAL_OBSERVATION_OR_REVISION_GATE")

                tr["effect_before_open"] = open_rows()
                opened = await call(2, "dispatch", {
                    "program": program("open-dialog-effect", 1, 1, ["CTRL", "O"]),
                    "current_observation_seq": 1, "current_binding_revision": 1})
                open_result = raw_result(opened)
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    rows = open_rows()
                    if rows:
                        tr["effect_after_open"] = rows
                        break
                    time.sleep(.1)
                if "effect_after_open" not in tr:
                    tr["effect_after_open"] = open_rows()
                tr["open_dispatch_result"] = open_result
                if open_result.get("status") != "completed":
                    raise RuntimeError("OPEN_DIALOG_DISPATCH_NOT_COMPLETED")
                opened_rows = tr["effect_after_open"]
                if len(opened_rows) != 1 or opened_rows[0]["window_id"] == root_id:
                    raise RuntimeError("INDEPENDENT_OPEN_DIALOG_EFFECT_NOT_UNIQUE")

                inspected = await call(3, "inspect_target", {"target": "calc",
                                            "screen_region": [0, 0, 1500, 900]})
                evidence = inspected.get("evidence", {})
                tr["dialog_evidence"] = evidence
                if (inspected.get("status") != "needs_review" or not inspected.get("review_id") or
                        evidence.get("window_id") != opened_rows[0]["window_id"] or
                        evidence.get("family_root") != root_id):
                    raise RuntimeError("DIALOG_INSPECTION_IDENTITY_GATE")
                reviewed = await call(4, "review_target", {"target": "calc",
                                          "window_id": evidence["window_id"],
                                          "review_id": inspected["review_id"]})
                tr["revision_dialog"] = reviewed.get("binding_revision")
                if (reviewed.get("status") != "target_reviewed" or
                        reviewed.get("binding_revision") != 2 or
                        reviewed.get("window_id") != evidence.get("window_id")):
                    raise RuntimeError("DIALOG_REVIEW_GATE")
                observed_dialog = await call(5, "observe", {"target": "calc",
                                                   "frame": "screen_physical_px",
                                                   "region": [0, 0, 1500, 900]})
                if observed_dialog.get("session", {}).get("binding_revision") != 2:
                    raise RuntimeError("DIALOG_OBSERVATION_SESSION_GATE")

                stale_dialog = await call(6, "dispatch", {
                    "program": program("stale-dialog-binding", 2, 1, ["F6"]),
                    "current_observation_seq": 2, "current_binding_revision": 2})
                tr["stale_dialog_result"] = raw_result(stale_dialog)
                if (tr["stale_dialog_result"].get("error") != "STALE_BINDING" or
                        tr["stale_dialog_result"].get("backend_emissions") != 0):
                    raise RuntimeError("STALE_DIALOG_BINDING_CONTROL_GATE")

                dismissed = await call(7, "dispatch", {
                    "program": program("dismiss-dialog-effect", 2, 2, ["ESC"]),
                    "current_observation_seq": 2, "current_binding_revision": 2})
                tr["dismiss_dispatch_result"] = raw_result(dismissed)
                release = tr["dismiss_dispatch_result"].get("execution", {}).get("releases", [])
                if tr["dismiss_dispatch_result"].get("status") != "completed" or not release or not all(
                        r.get("verified") and r.get("keys_down") == [] and r.get("buttons_down") == []
                        for r in release):
                    raise RuntimeError("DISMISS_DISPATCH_RELEASE_GATE")
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    rows = open_rows()
                    if not rows:
                        tr["effect_after_escape"] = rows
                        break
                    time.sleep(.1)
                tr.setdefault("effect_after_escape", open_rows())
                if tr["effect_after_escape"]:
                    raise RuntimeError("INDEPENDENT_DIALOG_DISMISSAL_EFFECT_NOT_OBSERVED")

                root_inspect = await call(8, "inspect_target", {"target": "calc",
                                                "screen_region": [0, 0, 1500, 900]})
                root_evidence = root_inspect.get("evidence", {})
                tr["root_return_evidence"] = root_evidence
                if (root_inspect.get("status") != "needs_review" or
                        root_evidence.get("window_id") != root_id or
                        root_evidence.get("family_root") != root_id):
                    raise RuntimeError("RETURN_TO_ROOT_INSPECTION_GATE")
                root_review = await call(9, "review_target", {"target": "calc",
                                              "window_id": root_id,
                                              "review_id": root_inspect["review_id"]})
                tr["revision_root"] = root_review.get("binding_revision")
                if root_review.get("status") != "target_reviewed" or root_review.get("binding_revision") != 3:
                    raise RuntimeError("RETURN_TO_ROOT_REVIEW_GATE")
                root_observation = await call(10, "observe", {"target": "calc",
                                                    "frame": "window_client",
                                                    "region": [0, 0, 160, 120]})
                if root_observation.get("session", {}).get("binding_revision") != 3:
                    raise RuntimeError("ROOT_OBSERVATION_SESSION_GATE")

                stale_root = await call(11, "dispatch", {
                    "program": program("stale-root-binding", 3, 2, ["F6"]),
                    "current_observation_seq": 3, "current_binding_revision": 3})
                tr["stale_root_result"] = raw_result(stale_root)
                if (tr["stale_root_result"].get("error") != "STALE_BINDING" or
                        tr["stale_root_result"].get("backend_emissions") != 0):
                    raise RuntimeError("STALE_ROOT_BINDING_CONTROL_GATE")

                final = await call(12, "dispatch", {
                    "program": program("fresh-root-neutral", 3, 3, ["ESC"]),
                    "current_observation_seq": 3, "current_binding_revision": 3})
                tr["final_dispatch_result"] = raw_result(final)
                final_release = tr["final_dispatch_result"].get("execution", {}).get("releases", [])
                if tr["final_dispatch_result"].get("status") != "completed" or not final_release or not all(
                        r.get("verified") and r.get("keys_down") == [] and r.get("buttons_down") == []
                        for r in final_release):
                    raise RuntimeError("FINAL_NEUTRAL_DISPATCH_GATE")
                tr["effect_final"] = open_rows()
                if tr["effect_final"]:
                    raise RuntimeError("OPEN_DIALOG_REAPPEARED")

                closed = await call(13, "close", {})
                close_done = True
                tr["close_release"] = closed.get("release", {})
                if (closed.get("status") != "closed" or closed.get("release_attempted") is not True or
                        closed.get("release", {}).get("verified") is not True or
                        closed.get("release", {}).get("keys_down") != [] or
                        closed.get("release", {}).get("buttons_down") != []):
                    raise RuntimeError("CLOSE_RELEASE_GATE")
                tr["retained_reads"] = []
                for index, prior in enumerate(tr["calls"], start=1):
                    result = await client.call_tool("interface_results", {"call_id": prior["call_id"]})
                    read_path = OUT / "mcp" / f"14-retained-{index:02d}.json"
                    digest, images = save_response(read_path, result)
                    retained = public_payload(result)
                    row = {"call_id": prior["call_id"], "state": retained.get("retained_call", {}).get("state"),
                           "operation_invoked": retained.get("operation_invoked"),
                           "response_sha256": digest, "images": images}
                    tr["retained_reads"].append(row)
                    if row["state"] != "finished" or row["operation_invoked"] is not False:
                        raise RuntimeError("RETAINED_READ_GATE:" + str(prior["call_id"]))
                    write_json(OUT / "trace.partial.json", tr)
                tr["decision"] = "PASS_PUBLIC_MCP_MODAL_EFFECT_SCOPED"
                write_json(OUT / "trace.partial.json", tr)
            except Exception:
                write_json(OUT / "trace.partial.json", tr)
                if not close_done:
                    try:
                        closed = await call(99, "close", {})
                        tr["close_after_exception"] = closed
                        close_done = True
                    except Exception as close_error:
                        tr["close_after_exception_error"] = repr(close_error)
                raise
    return tr


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "mcp").mkdir()
    (OUT / "server-receipts").mkdir()
    actual_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if actual_hash != RUNNER_SHA256:
        raise RuntimeError("RUNNER_HASH_MISMATCH")
    write_json(OUT / "environment.json", {
        "source_main_reference": SOURCE_COMMIT,
        "source_closure_commit": "51c04e1208014406b7422c5291c97e7023ba68f4",
        "relevant_source_git_blobs": {
            "runtime/cli_v1/mcp_server.py": "82a7841b53a0618ecbf74b4ead8157a42b62112e",
            "runtime/cli_v1/mcp_session.py": "b27dbc6c19d0a2df2b77c81a140cdc16b02d2509",
            "runtime/cli_v1/api.py": "6318f0d2fe0b0533d694175e2521eb86946dbed1",
            "runtime/cli_v1/observe.py": "08460ae506afcd0f9ad89b91064d121c55c5b419",
            "runtime/cli_v1/x11_target_review.py": "3804964e9b7f3a933f0cf060b7552efc09073403",
            "runtime/backends/x11_v1/session.py": "e973b2f3f827951634344a320cd833a80a899d9e",
            "runtime/core_v1/contract.py": "87154518107e4231a6f8ec06e976d2856b375d1d"},
        "runner_sha256": actual_hash,
        "image_id": IMAGE, "display": DISPLAY, "network": "none",
        "model_calls": 0, "network_calls": 0, "authority_granted": False})
    xvfb = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1600x1000x24"], env=ENV,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True)
    wm = None
    calc = None
    trace = None
    try:
        time.sleep(.5)
        wm = subprocess.Popen(["openbox", "--replace"], env=ENV,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              start_new_session=True)
        time.sleep(.7)
        calc, root = launch_calc()
        write_json(OUT / "calc-identity.json", root)
        write_json(OUT / "targets.json", {"calc": root["window_id"]})
        tip_before = [w for w in snapshot() if "tip of the day" in w["title"].lower()]
        tip_action = None
        if tip_before:
            act = run(["xdotool", "windowactivate", "--sync", str(tip_before[0]["window_id"])])
            key = run(["xdotool", "key", "Escape"])
            time.sleep(.5)
            tip_action = {"window_id": tip_before[0]["window_id"],
                          "activate_rc": act.returncode, "escape_rc": key.returncode,
                          "tip_windows_after": [w for w in snapshot() if "tip of the day" in w["title"].lower()]}
        root_still = window_info(root["window_id"])
        write_json(OUT / "startup-dialog.json", {"tip_before": tip_before,
                    "dismissal": tip_action, "root_after": root_still,
                    "root_xid_preserved": root_still["window_id"] == root["window_id"]})
        if root_still["window_id"] != root["window_id"]:
            raise RuntimeError("CALC_ROOT_CHANGED_DURING_STARTUP_PREP")
        focus = run(["xdotool", "windowactivate", "--sync", str(root["window_id"])])
        write_json(OUT / "startup-focus.json", {"returncode": focus.returncode,
                    "active_window": run(["xdotool", "getactivewindow"]).stdout.strip()})
        if focus.returncode != 0:
            raise RuntimeError("CALC_ROOT_FOCUS_SETUP_FAILED")
        trace = asyncio.run(sequence(root["window_id"]))
        owned = {xvfb.pid, wm.pid, calc.pid}
        write_json(OUT / "owned-pids-before-cleanup.json", {"pids": sorted(owned),
                    "states": {str(p): proc_table().get(p) for p in sorted(owned)}})
        result = {"decision": trace.get("decision", "HOLD_INCOMPLETE"),
                  "trace": trace, "authority_granted": False,
                  "model_calls": 0, "network_calls": 0}
    except Exception as error:
        if trace is None and (OUT / "trace.partial.json").exists():
            try:
                trace = json.loads((OUT / "trace.partial.json").read_text(encoding="utf-8"))
            except Exception:
                trace = {"decision": "HOLD_PARTIAL_TRACE_UNREADABLE"}
        if trace is None:
            trace = {"calls": [], "model_calls": 0, "network_calls": 0,
                     "authority_granted": False}
        trace["stop_reason"] = repr(error)
        if isinstance(trace, dict):
            trace["decision"] = "STOP_CONSTRUCTION_EXCEPTION_NO_RETRY"
            write_json(OUT / "trace.partial.json", trace)
        result = {"decision": "STOP_CONSTRUCTION_EXCEPTION_NO_RETRY",
                  "error": repr(error), "trace": trace or {},
                  "authority_granted": False, "model_calls": 0, "network_calls": 0}
    finally:
        for proc in (calc, wm, xvfb):
            if proc is not None:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except (ProcessLookupError, PermissionError):
                    pass
        time.sleep(.4)
        write_json(OUT / "post-cleanup.json", {
            "visible_windows": snapshot() if Path("/tmp/.X11-unix/X151").exists() else [],
            "x_socket_exists": Path("/tmp/.X11-unix/X151").exists(),
            "launcher_states": {str(p.pid): proc_table().get(p.pid)
                                for p in (calc, wm, xvfb) if p is not None},
            "authority_granted": False})
    write_json(OUT / "result.json", result)
    print(json.dumps({"decision": result["decision"], "error": result.get("error"),
                      "calls": [x.get("operation") for x in result.get("trace", {}).get("calls", [])],
                      "root": result.get("trace", {}).get("root_window_id"),
                      "binding_revisions": [result.get("trace", {}).get(k) for k in
                                            ("revision_initial", "revision_dialog", "revision_root")],
                      "open_before": len(result.get("trace", {}).get("effect_before_open", [])),
                      "open_after": len(result.get("trace", {}).get("effect_after_open", [])),
                      "open_after_escape": len(result.get("trace", {}).get("effect_after_escape", [])),
                      "stale_errors": [result.get("trace", {}).get(k, {}).get("error") for k in
                                       ("stale_dialog_result", "stale_root_result")]}, sort_keys=True))
    return 0 if result["decision"] == "PASS_PUBLIC_MCP_MODAL_EFFECT_SCOPED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
