"""Frozen three-arm visual-memory ablation on actual Chromium input."""
import contextlib
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/action-grounded-memory-ablation-live-01"
PLAN = HERE / "action_grounded_memory_ablation_live_v1_prereg.json"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def wait_terminal(events, identifier):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        row = next((item for item in reversed(events)
                    if item.get("event") == "terminal" and item.get("id") == identifier), None)
        if row is not None: return row
        time.sleep(.001)
    raise RuntimeError("terminal missing")


def prompt(plan):
    return ("Task: Submit the prefilled Value record using the real Save control in the "
            "Submission form. The Preview card must remain untouched. Image 1 is the exact "
            "current 1280x800 screen. If Image 2 exists, it is prior visual memory. The same "
            "retained evidence facts apply in every arm: target name save_form; prior action "
            "completed with empty verified release; independent effect submission_title_exactly_visible; "
            "archived evidence grants no current authority. Select from current pixels and abstain "
            "if the real target is not distinguishable.")


def run_case(plan, fixture, row):
    from executor_v13 import Executor
    from semantic_probe_backend_v3 import Backend, suite
    from visual_memory_model_v1 import invoke

    case = OUT / row["name"]; case.mkdir(); (case / "empty-workspace").mkdir()
    events, actions = [], []
    session = backend = executor = None

    def emit(event): event["runtime_emit_ns"] = time.perf_counter_ns(); events.append(event)
    def submit(identifier, program):
        executor.submit(identifier, program, backend.sequence, time.perf_counter_ns() + 8_000_000_000)
        accepted = next(event for event in events if event.get("event") == "accepted" and event.get("id") == identifier)
        result = {"id": identifier, "program": program, "accepted": accepted,
                  "terminal": wait_terminal(events, identifier)}
        actions.append(result); return result

    result = {"name": row["name"], "scenario": row["scenario"], "arm": row["arm"],
              "ordinal": row["ordinal"], "status": "STARTED", "retry_count": 0}
    try:
        with (case / "setup.txt").open("w") as diagnostics, contextlib.redirect_stdout(diagnostics):
            session = suite.Session()
            args = [plan["chromium"], "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
                    "--no-first-run", "--no-default-browser-check", "--disable-background-networking",
                    "--disable-component-update", "--disable-sync", "--password-store=basic",
                    f"--user-data-dir={session.tmp}/profile", "about:blank"]
            session.spawn(args, stdout=diagnostics, stderr=diagnostics)
            session.wait_window("about:blank", 20); session.focus("about:blank")
            backend = Backend(session, case, emit); executor = Executor(backend, emit)
        backend.snapshot("initial", 0)
        submit(f"nav-{row['ordinal']}", [{"op": "chord", "modifier": "Control_L", "key": "l"},
            {"op": "text", "text": fixture.url(row["scenario"])}, {"op": "key", "key": "Return"},
            {"op": "wait_title", "contains": f"AI MEMORY {row['scenario']} READY", "timeout_ms": 1500}])
        backend.snapshot("memory-current", 0); current = events[-1]
        current_path = case / Path(current["image"]).name
        images = [current_path]
        if row["arm"] == "full_frame": images.append(HERE / plan["memory"]["full_frame_path"])
        elif row["arm"] == "action_crop": images.append(HERE / plan["memory"]["action_crop_path"])
        before_records = len(fixture.records())
        model = invoke(case / "model", prompt(plan), images, case / "empty-workspace")
        decision = model["decision"]; action = None
        if decision["status"] == "target_reference":
            backend.snapshot("post-model-current", 0); refreshed = events[-1]
            if (refreshed.get("exact") is not True or refreshed.get("pointer_binding") is None
                    or refreshed["pointer_binding"] != current["pointer_binding"]):
                raise RuntimeError("current binding changed after model")
            action = submit(f"select-{row['ordinal']}", [
                {"op": "pointer_click", "x": decision["x"], "y": decision["y"], "duration_ms": 80},
                {"op": "settle", "quiet_ms": 100, "timeout_ms": 700}, {"op": "observe"}])
        deadline = time.monotonic() + .8
        while time.monotonic() < deadline and len(fixture.records()) == before_records: time.sleep(.01)
        observed = fixture.records()[before_records:]
        correct = len(observed) == 1 and observed[0]["exact"] is True
        wrong = len(observed) == 1 and observed[0]["kind"] == "decoy"
        result.update(status="COMPLETED", current_observation=current,
                      current_image_sha256=sha(current_path), prompt_sha256=hashlib.sha256(prompt(plan).encode()).hexdigest(),
                      model=model, images=[{"path": str(path.relative_to(HERE)).replace("\\", "/") if path.is_relative_to(HERE) else path.name,
                                           "sha256": sha(path)} for path in images],
                      action=action, oracle_records=observed, correct=correct,
                      wrong_target_action=wrong, no_effect=len(observed) == 0,
                      release_ok=action is None or (action["terminal"]["release"]["verified"] is True
                          and action["terminal"]["release"]["keys_down"] == []
                          and action["terminal"]["release"]["buttons_down"] == []))
    except Exception as error:
        result.update(status="FAILED", error=f"{type(error).__name__}: {error}")
    finally:
        (case / "events.json").write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8", newline="\n")
        result["actions"] = actions
        if session is not None: session.close()
        (case / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def main():
    from visual_memory_fixture_v1 import Fixture
    from visual_memory_model_v1 import invoke
    plan = read(PLAN)
    if OUT.exists(): raise FileExistsError(OUT)
    for name, digest in plan["source_sha256"].items():
        if sha(HERE / name) != digest: raise ValueError("source hash changed: " + name)
    for key in ("full_frame_path", "action_crop_path"):
        if sha(HERE / plan["memory"][key]) != plan["memory"][key.replace("path", "sha256")]:
            raise ValueError("memory artifact changed")
    OUT.mkdir(); (OUT / "prereg.json").write_bytes(PLAN.read_bytes())
    (OUT / "preflight-workspace").mkdir()
    try:
        preflight = invoke(OUT / "schema-preflight", prompt(plan),
                           [HERE / plan["memory"]["full_frame_path"]], OUT / "preflight-workspace")
    except Exception as error:
        preflight = {"status": "FAILED", "error": f"{type(error).__name__}: {error}"}
        report = {"schema": "action-grounded-memory-ablation-live-report-v1",
                  "completed": False, "schema_preflight": preflight, "results": [],
                  "all_records": [], "allocation_retries": 0, "formal_pass": False,
                  "decision": "INCOMPLETE_RETAIN_FIRST_OUTCOME"}
        (OUT / "preflight.json").write_text(json.dumps(preflight, indent=2) + "\n",
                                             encoding="utf-8", newline="\n")
        (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                          encoding="utf-8", newline="\n")
        print(json.dumps({"completed": False, "formal_pass": False,
                          "decision": report["decision"]}, indent=2))
        return 2
    (OUT / "preflight.json").write_text(json.dumps(preflight, indent=2) + "\n",
                                         encoding="utf-8", newline="\n")
    fixture = Fixture(OUT / "fixture", plan["seed"]); results = []
    try:
        for row in plan["schedule"]:
            result = run_case(plan, fixture, row); results.append(result)
            if result["status"] != "COMPLETED": break
    finally: fixture.close()
    completed = len(results) == len(plan["schedule"]) and all(row["status"] == "COMPLETED" for row in results)
    report = {"schema": "action-grounded-memory-ablation-live-report-v1", "completed": completed,
              "schema_preflight": preflight,
              "results": results, "all_records": fixture.records(), "allocation_retries": 0,
              "formal_pass": False, "decision": "INCOMPLETE_RETAIN_FIRST_OUTCOME"}
    if completed:
        hashes = {scenario: {row["current_image_sha256"] for row in results if row["scenario"] == scenario}
                  for scenario in plan["scenarios"]}
        mechanics = all(len(value) == 1 for value in hashes.values()) and all(row["release_ok"] for row in results)
        report["formal_pass"] = mechanics
        stats = {arm: {"correct": sum(row["correct"] for row in results if row["arm"] == arm),
                       "wrong": sum(row["wrong_target_action"] for row in results if row["arm"] == arm),
                       "input_tokens": sum(row["model"]["usage"]["input_tokens"] for row in results if row["arm"] == arm),
                       "images": sum(row["model"]["visible_images_submitted"] for row in results if row["arm"] == arm)}
                 for arm in plan["arms"]}
        report["stats"] = stats
        crop = stats["action_crop"]
        report["decision"] = ("CROP_ELIGIBLE_FOR_TRANSFER" if mechanics and crop["correct"] == 3
            and crop["wrong"] == 0 and crop["correct"] >= stats["full_frame"]["correct"]
            and crop["correct"] >= stats["no_memory"]["correct"]
            and crop["input_tokens"] < stats["full_frame"]["input_tokens"]
            else "DO_NOT_TRANSFER_CROP")
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"completed": completed, "formal_pass": report["formal_pass"],
                      "decision": report["decision"]}, indent=2))
    return 0 if completed else 2


if __name__ == "__main__": raise SystemExit(main())
