"""Engineering probe: six-task persistent reuse/invalidation/repair mechanics."""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from append_checkpoint_v1 import load
from durable_submit_v4 import initialize, run
from received_continuation_v1 import start
from received_exchange_v2 import request_once


HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "integrated-efficiency-persistent-mechanics-05"
SEED = 991026
POINTS = {"A": {"field": [226, 401], "submit": [376, 401]},
          "B": {"field": [650, 558], "submit": [688, 634]}}


def first(records, event):
    return next(row for row in records if row.get("event") == event)


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    runtime = OUT / "runtime"
    errors = (OUT / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "integrated_efficiency_socket_v1.py"),
        "integrated-efficiency-chromium-v1", "serve", "--", "--app", "chromium",
        "--seed", str(SEED), "--out", str(runtime),
    ], stdout=subprocess.PIPE, stderr=errors, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="integrated-persistent-mechanics-")
    journal = Path(temporary.name) / "journal.jsonl"
    programs = []
    try:
        endpoint = json.loads(process.stdout.readline())
        initial = request_once(endpoint["socket"], start(endpoint["socket"]),
                               {"events": ["observation"], "timeout": 30})
        ready = first(initial["reply"]["records"], "ready")
        initialize(journal, initial["continuation"])

        def call(spec):
            result = run(journal, spec)
            assert result["state"]["pending"] is None
            return result

        def clock():
            result = call({"command": {"op": "clock"}, "timeout": 3})
            return result["state"]["last_resolution"]["clock"]

        def submit(label, steps, timeout=10):
            current = clock()
            result = call({"command": {"op": "submit",
                "expected_sequence": current["sequence"],
                "valid_until_ns": current["runtime_ns"] + 10_000_000_000,
                "steps": steps}, "timeout": timeout})
            records = result["reply"]["records"]
            terminal = first(records, "terminal")
            programs.append({"label": label, "terminal": terminal,
                             "pointer_admissions": [row for row in records if row.get("event") ==
                                                     "pointer_admission"],
                             "target_checks": [row for row in records if row.get("event") ==
                                               "target_handle_checked"],
                             "point_mints": [row for row in records if row.get("event") ==
                                             "target_handle_minted_from_point"]})
            return result

        def navigate(task):
            result = submit("navigate-" + task["task_id"], [
                {"op": "chord", "modifier": "Control_L", "key": "l"},
                {"op": "text", "text": task["url"]},
                {"op": "key", "key": "Return"},
                {"op": "settle", "quiet_ms": 80, "timeout_ms": 500},
            ])
            assert first(result["reply"]["records"], "terminal")["status"] == "completed"
            observed = submit("source-" + task["task_id"], [{"op": "observe"}])
            return first(observed["reply"]["records"], "observation")

        def mint(layout, source):
            aliases = {"field": "field_" + layout.lower(), "submit": "submit_" + layout.lower()}
            for kind in ("field", "submit"):
                result = submit("mint-" + aliases[kind], [{
                    "op": "target_handle_mint_from_point", "name": aliases[kind],
                    "coordinate_frame": "window_content", "source_sequence": source["sequence"],
                    "point": POINTS[layout][kind],
                    "region_size": [24, 38] if kind == "field" else [24, 14],
                    "ttl_ms": 300000, "freshness_ms": 1500, "search_radius": 0,
                    "allowed_transformations": ["window_translation"],
                }])
                records = result["reply"]["records"]
                assert first(records, "terminal")["status"] == "completed"
                assert len([row for row in records if row.get("event") ==
                            "target_handle_minted_from_point"]) == 1
            return aliases

        def check(alias, offset, label):
            result = submit(label, [{"op": "observe_target_handle",
                                     "target_handle": alias, "offset": offset}])
            records = result["reply"]["records"]
            return first(records, "target_handle_checked")

        def execute_task(task, aliases):
            field = check(aliases["field"], [12, 11], "check-field-" + task["task_id"])
            assert field["eligible"] is True and field["status"] in {"VALID", "REVALIDATED"}
            entered = submit("enter-" + task["task_id"], [
                {"op": "pointer_click_target", "target_handle": aliases["field"],
                 "offset": [12, 11], "button": 1, "duration_ms": 80},
                {"op": "chord", "modifier": "Control_L", "key": "a"},
                {"op": "text", "text": task["token"]},
                {"op": "settle", "quiet_ms": 80, "timeout_ms": 500},
            ])
            assert first(entered["reply"]["records"], "terminal")["status"] == "completed"
            control = check(aliases["submit"], [12, 7], "check-submit-" + task["task_id"])
            assert control["eligible"] is True and control["status"] in {"VALID", "REVALIDATED"}
            saved = submit("submit-" + task["task_id"], [
                {"op": "pointer_click_target", "target_handle": aliases["submit"],
                 "offset": [12, 7], "button": 1, "duration_ms": 80},
                {"op": "settle", "quiet_ms": 80, "timeout_ms": 500},
            ])
            assert first(saved["reply"]["records"], "terminal")["status"] == "completed"

        aliases = None
        invalidation = None
        for index, task in enumerate(ready["goal"]["tasks"]):
            source = navigate(task)
            if index == 0:
                aliases = mint("A", source)
            elif index == 3:
                old = check(aliases["field"], [12, 11], "old-field-invalidation")
                invalidation = {"status": old["status"], "eligible": old["eligible"],
                                "sequence": old.get("sequence")}
                assert old["eligible"] is False and old["status"] in {"MISSING", "STALE"}
                aliases = mint("B", source)
            execute_task(task, aliases)

        state = load(journal)["continuation"]
        finished = request_once(endpoint["socket"], state, {
            "events": ["independent_evaluation"], "timeout": 10,
            "command": {"op": "finish"}, "request_id": "finish-persistent-mechanics"})
        evaluation = first(finished["reply"]["records"], "independent_evaluation")
        assert evaluation["success"] is True and evaluation["record_count"] == 6
        assert invalidation and invalidation["eligible"] is False
        old_program = next(row for row in programs if row["label"] == "old-field-invalidation")
        assert old_program["pointer_admissions"] == []
        target_programs = [row for row in programs if row["label"].startswith(("enter-", "submit-"))]
        assert len(target_programs) == 12
        assert all(sum(event["operation"] == "button_down"
                       for event in row["pointer_admissions"]) == 1 for row in target_programs)
        assert all(row["terminal"]["release"]["verified"] is True
                   and row["terminal"]["release"]["keys_down"] == []
                   and row["terminal"]["release"]["buttons_down"] == [] for row in programs)
        shutil.copy2(journal, OUT / "journal.jsonl")
        report = {"schema": "integrated_efficiency_persistent_mechanics_v1",
                  "passed": True, "seed": SEED, "human_inspected_points": POINTS,
                  "model_calls": 0, "tasks_completed": 6, "invalidation": invalidation,
                  "old_target_pointer_admissions": 0,
                  "target_button_down_admissions": sum(
                      event["operation"] == "button_down" for row in target_programs
                      for event in row["pointer_admissions"]),
                  "programs": programs, "independent_evaluation": evaluation,
                  "claim": "engineering mechanics only; excluded from formal comparison"}
        (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                          encoding="utf-8", newline="\n")
        print(json.dumps({"passed": True, "tasks": 6, "invalidation": invalidation,
                          "programs": len(programs)}, indent=2))
    finally:
        temporary.cleanup()
        errors.close()
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=10)


if __name__ == "__main__":
    main()
