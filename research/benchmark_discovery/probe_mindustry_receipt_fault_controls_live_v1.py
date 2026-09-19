"""Exercise real X11 unavailable-binding and resize controls without a model."""
import json
import subprocess
import sys
import uuid
from pathlib import Path


HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_control"
sys.path.insert(0, str(LIVE))

from unix_json_deadline import exchange


OUT = HERE / "results/mindustry-receipt-fault-controls-03"
LINUX_ROOT = "/home/taka/agent-interface-bench-feasibility"


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n",
                    encoding="utf-8", newline="\n")


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    stderr = (OUT / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "mindustry_single_tile_socket_v3.py"),
        "serve", "--", "--root", LINUX_ROOT, "--out", str(OUT / "runtime")],
        stdout=subprocess.PIPE, stderr=stderr, text=True)
    endpoint = None
    cursor = 0
    calls = []

    def query(events, command=None, timeout=30):
        nonlocal cursor
        request = {"after": cursor, "events": events, "timeout": timeout}
        if command is not None:
            request.update(command=command, request_id=uuid.uuid4().hex)
        reply = exchange(endpoint["socket"], request, timeout=timeout + 3)
        calls.append({"request": request, "reply": reply})
        cursor = reply.get("cursor", cursor)
        dump(OUT / "calls.json", calls)
        return reply

    def submit(identifier, steps):
        clock_reply = query(["clock"], {"op": "clock"}, 3)
        clock = next(row for row in clock_reply["records"]
                     if row.get("event") == "clock")
        return query(["terminal"], {"op": "submit", "id": identifier,
            "expected_sequence": clock["sequence"],
            "valid_until_ns": clock["runtime_ns"] + 10_000_000_000,
            "steps": steps}, 15)

    try:
        endpoint = json.loads(process.stdout.readline())
        dump(OUT / "endpoint.json", endpoint)
        initial_reply = query(["observation"], timeout=30)
        initial = next(row for row in initial_reply["records"]
                       if row.get("event") == "observation")
        assert initial["pointer_binding"] is not None
        initial_geometry = initial["pointer_binding"]["geometry"]

        submit("unbound", [{"op": "test_focus_unbound"}, {"op": "observe"}])
        unbound_events = json.loads((OUT / "calls.json").read_text())[-1]["reply"]["records"]
        unbound = next(row for row in reversed(unbound_events)
                       if row.get("event") == "observation")
        assert unbound["pointer_binding"] is None

        restored_focus_reply = submit(
            "restore-unbound", [{"op": "test_focus_unbound_restore"},
                                {"op": "observe"}])
        restored_focus = next(row for row in reversed(restored_focus_reply["records"])
                              if row.get("event") == "observation")
        assert restored_focus["pointer_binding"] is not None
        assert restored_focus["pointer_binding"]["geometry"] == initial_geometry

        resized_reply = submit(
            "resize", [{"op": "test_surface_resize", "width_delta": -64},
                       {"op": "observe"}])
        resized = next(row for row in reversed(resized_reply["records"])
                       if row.get("event") == "observation")
        assert resized["pointer_binding"] is not None
        assert resized["pointer_binding"]["geometry"][2] == initial_geometry[2] - 64

        restored_resize_reply = submit(
            "restore-resize", [{"op": "test_surface_resize_restore"},
                               {"op": "observe"}])
        restored_resize = next(row for row in reversed(restored_resize_reply["records"])
                               if row.get("event") == "observation")
        assert restored_resize["pointer_binding"]["geometry"] == initial_geometry

        finish = query(["independent_evaluation"], {"op": "finish"}, 20)
        code = process.wait(timeout=30)
        evaluation = next(row for row in finish["records"]
                          if row.get("event") == "independent_evaluation")
        runtime_events = [json.loads(line) for line in
                          (OUT / "runtime/events.jsonl").read_text().splitlines()]
        assert code == 0
        assert evaluation["contract_satisfied"] is False
        assert not any(row.get("event") == "pointer_admission" and
                       row.get("operation") == "button_down"
                       for row in runtime_events)
        result = {"passed": True, "initial_geometry": initial_geometry,
                  "unbound_pointer_binding": unbound["pointer_binding"],
                  "restored_focus_binding": restored_focus["pointer_binding"],
                  "resized_geometry": resized["pointer_binding"]["geometry"],
                  "restored_geometry": restored_resize["pointer_binding"]["geometry"],
                  "socket_exchanges": len(calls), "model_calls": 0,
                  "button_downs": 0, "bridge_exit_code": code,
                  "task_success": evaluation["contract_satisfied"],
                  "scope": "fault-control feasibility only; no model or receipt decision"}
        dump(OUT / "result.json", result)
        print(json.dumps(result, indent=2))
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        stderr.close()


if __name__ == "__main__":
    main()
