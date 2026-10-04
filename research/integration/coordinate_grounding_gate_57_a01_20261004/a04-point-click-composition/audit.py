from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
REPO = HERE.parents[3]


def blob(oid: str) -> bytes:
    return subprocess.check_output(["git", "cat-file", "blob", oid], cwd=REPO)


def blob_at(commit: str, path: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"{commit}:{path}"], cwd=REPO, text=True).strip()


pins = json.loads((HERE / "SOURCE_PINS.json").read_text(encoding="utf-8"))
assert pins["schema"] == "a04-point-click-composition-source-pins-v1"
assert blob_at(pins["source_commit"], pins["point_validator"]["path"]) == pins["point_validator"]["git_blob"]
assert hashlib.sha1(b"blob " + str(len(blob(pins["point_validator"]["git_blob"]))).encode() + b"\0" + blob(pins["point_validator"]["git_blob"])).hexdigest() == pins["point_validator"]["git_blob"]
assert blob_at(pins["source_commit"], pins["source_mint_route_reference"]["path"]) == pins["source_mint_route_reference"]["git_blob"]
assert pins["source_mint_route_reference"]["executed"] is True
assert blob_at(pins["source_commit"], pins["legacy_adapter_reference"]["path"]) == pins["legacy_adapter_reference"]["git_blob"]
for path, oid in pins["runtime_sources"].items():
    assert blob_at(pins["source_commit"], path) == oid
    assert hashlib.sha1(b"blob " + str(len(blob(oid))).encode() + b"\0" + blob(oid)).hexdigest() == oid

inputs = json.loads((HERE / "INPUTS.json").read_text(encoding="utf-8"))
a03 = json.loads((PACKAGE / "a03-context-crops" / "RESULT.json").read_text(encoding="utf-8"))
result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
assert len(inputs["cases"]) == len(result["cases"]) == 5
context_by_task = {row["task"]: row["padded_crop"]["box"] for row in a03["cases"]}
for source, row in zip(inputs["cases"], result["cases"], strict=True):
    assert row["task"] == source["task"]
    image_path = (PACKAGE / "a02-retained-screenshot-grounding" / source["image_file"]).resolve()
    raw = image_path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == source["image_sha256"]
    assert hashlib.sha1(b"blob " + str(len(blob(source["image_git_blob"]))).encode() + b"\0" + blob(source["image_git_blob"])).hexdigest() == source["image_git_blob"]
    with Image.open(image_path) as f:
        image = f.convert("RGB")
    point = source["field_point"]
    width, height = row["command"]["region_size"]
    expected_box = [point[0] - width // 2, point[1] - height // 2, width, height]
    expected_offset = [width // 2, height // 2]
    box = row["box"]
    context = context_by_task[source["task"]]
    assert box == expected_box and row["offset"] == expected_offset
    assert box[0] >= context[0] and box[1] >= context[1]
    assert box[0] + box[2] <= context[0] + context[2]
    assert box[1] + box[3] <= context[1] + context[3]
    patch_bytes = image.crop((box[0], box[1], box[0] + box[2], box[1] + box[3])).tobytes()
    digest = hashlib.sha256(patch_bytes).hexdigest()
    assert row["patch_sha256"] == row["mint"]["patch_sha256"] == row["resolution"]["patch_sha256"] == digest
    route = row["mint_route"]
    route_record = route["result"]
    assert route["executed"] is True and route["accepted"] is True
    assert route_record["source_sequence"] == 1 and route_record["fresh_sequence"] == 2
    assert route_record["source_point"] == point and route_record["derived_box"] == box
    assert route_record["derived_offset"] == expected_offset
    assert route_record["fresh_patch_exact"] is True
    assert route_record["source_patch_sha256"] == route_record["fresh_patch_sha256"] == digest
    assert row["accepted"] and row["status"] == row["mint"]["status"] == row["resolution"]["status"] == "VALID"
    assert row["resolution"]["eligible"] is True
    assert row["alias"] == row["command"]["name"] == row["action_spec"]["target_handle"] == row["resolution"]["handle"]
    assert row["proposal_point"] == point == row["command"]["point"] == row["resolution"]["point"] == row["action_spec"]["point"]
    assert row["action_spec"]["box"] == box and row["action_spec"]["offset"] == expected_offset
    assert row["action_specs"] == [row["action_spec"]]
    assert row["command"]["source_sequence"] == route_record["source_sequence"] == 1
    assert row["mint"]["created_sequence"] == route_record["fresh_sequence"] == 2

negative = result["negative_cases"]
fixed = negative["fixed_offset"]
assert not fixed["accepted"] and fixed["action_specs"] == []
assert fixed["stage"] == "identity_consistency"
assert fixed["resolution"]["point"] == [230, 409] and fixed["resolution"]["point"] != [250, 401]
wrong_alias = negative["wrong_alias"]
assert not wrong_alias["accepted"] and wrong_alias["action_specs"] == []
assert wrong_alias["status"] == "MISSING" and wrong_alias["stage"] == "fresh_resolution"
expected = {"changed_patch": ("source_mint_route", "MISSING"),
            "focus_changed": ("source_mint_route", "SCOPE_MISMATCH"),
            "surface_changed": ("source_mint_route", "SCOPE_MISMATCH"),
            "stale": ("fresh_resolution", "STALE")}
assert set(result["ineligible_cases"]) == set(expected)
for name, (stage, status) in expected.items():
    case = result["ineligible_cases"][name]
    assert not case["accepted"] and case["action_specs"] == []
    assert (case["stage"], case["status"]) == (stage, status)
    assert case["mint_route"]["executed"] is True
assert result["input_dispatch_count"] == result["gui_call_count"] == result["model_call_count"] == 0
runs = json.loads((HERE / "RUNS.json").read_text(encoding="utf-8"))
assert runs["tests"]["exit_code"] == runs["pycompile"]["exit_code"] == 0
test_stderr = (HERE / runs["tests"]["stderr_path"]).read_text(encoding="utf-8")
assert "Ran 4 tests" in test_stderr and "OK" in test_stderr
print(json.dumps({"status": "PASS_A04_POINT_CLICK_COMPOSITION_AUDIT",
                  "accepted_proposals": 5, "inert_negative_cases": 6,
                  "pinned_runtime_sources": len(pins["runtime_sources"]),
                  "point_validator_blob": pins["point_validator"]["git_blob"],
                  "input_dispatch_count": 0}, sort_keys=True))
