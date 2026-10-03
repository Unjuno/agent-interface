"""One finite ordinary engineering comparison; explicit standalone entry only."""
import copy
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import platform

HERE = Path(__file__).resolve().parent


def load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def execute_case(runtime, spec, case):
    now = 0
    calls = {name: [] for name in ("observe", "admit", "execute", "verify_effect")}
    timeline = []

    def observe(request):
        nonlocal now
        index = len(calls["observe"])
        calls["observe"].append(copy.deepcopy(request))
        now = (10, 100, 200)[index]
        response = {"sequence": index + 1, "captured_ns": case["captures"][index],
                    "surface": "form", "predicates": {"phase": index},
                    "evidence_ref": f"frame-{index + 1}",
                    "evidence_digest": f"digest-{index + 1}"}
        timeline.append({"callback": "observe", "returned_ns": now,
                         "response": copy.deepcopy(response)})
        return response

    def admit(request):
        calls["admit"].append(copy.deepcopy(request))
        return {"eligible": True, "status": "revalidated", "authorization": "one-use",
                "expected_sequence": request["observation"]["sequence"],
                "valid_until_ns": 1_000_000}

    def execute(request):
        nonlocal now
        calls["execute"].append(copy.deepcopy(request))
        index = len(calls["execute"])
        now = (20, 110)[index - 1]
        timeline.append({"callback": "execute", "returned_ns": now})
        return {"status": "completed", "action_id": f"action-{index}",
                "effect_ref": f"effect-{index}",
                "release": {"verified": True, "keys_down": [], "buttons_down": []}}

    def verify(request):
        calls["verify_effect"].append(copy.deepcopy(request))
        return {"status": "succeeded", "evidence_ref": request["observation"]["evidence_ref"]}

    original = json.dumps(spec, sort_keys=True, ensure_ascii=True, allow_nan=False)
    try:
        receipt = runtime.run(spec, {"observe": observe, "admit": admit,
                                    "execute": execute, "verify_effect": verify,
                                    "cancelled": lambda: False}, clock=lambda: now)
        result = {"kind": "receipt", "receipt": receipt}
    except Exception as error:
        result = {"kind": "exception", "exception_type": type(error).__name__,
                  "message": str(error)}
    return {"case": copy.deepcopy(case), "calls": calls, "timeline": timeline,
            "input_unchanged": json.dumps(spec, sort_keys=True, ensure_ascii=True,
                                          allow_nan=False) == original, "result": result}


def main():
    freeze_bytes = (HERE / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    for name, record in freeze["files"].items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == record["sha256"], name
    cases = json.loads((HERE / "cases.json").read_bytes())
    interface = json.loads((HERE / "interface.json").read_bytes())
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    raw = HERE / "raw.jsonl"
    with raw.open("x", encoding="utf-8", newline="\n") as stream:
        for source in ("baseline", "candidate"):
            path = HERE / f"{source}-source/compiled_gui.py"
            runtime = load_file("frozen_" + source, path)
            for case in cases:
                row = execute_case(runtime, copy.deepcopy(interface), case)
                row.update(source=source, source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                           freeze_sha256=hashlib.sha256(freeze_bytes).hexdigest())
                stream.write(json.dumps(row, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n")
    receipt = {"kind": "ordinary deterministic engineering comparison",
               "started_utc": started,
               "completed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "python": platform.python_version(), "platform": platform.platform(),
               "rows": len(cases) * 2, "formal_allocations": 0,
               "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
               "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest()}
    (HERE / "RUN_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
