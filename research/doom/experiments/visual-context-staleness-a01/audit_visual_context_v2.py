"""Re-audit retained visual-context evidence from original bytes and transcript.

This is a post-run audit. It never starts WSLc, the game, a model, or an input
executor. Pillow is required only for decoding the retained PNGs to RGB bytes.
"""
import hashlib
import json
import pathlib
import re
import sys

from PIL import Image


ROOT = pathlib.Path(__file__).resolve().parent
errors = []


def check(condition, message):
    if not condition:
        errors.append(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def verify_frozen_file(path, frozen):
    data = path.read_bytes()
    check(len(data) == frozen["bytes"], f"{path.name}: frozen length mismatch")
    check(sha256(data) == frozen["sha256"], f"{path.name}: frozen SHA-256 mismatch")
    check(git_blob(data) == frozen["git_blob"], f"{path.name}: frozen Git blob mismatch")


freeze = read_json(ROOT / "FREEZE.json")
manifest_path = ROOT / "SHA256SUMS"
manifest = {}
for line_number, line in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), 1):
    if not line.strip():
        continue
    try:
        expected, relative = line.split("  ", 1)
    except ValueError:
        check(False, f"SHA256SUMS:{line_number}: malformed entry")
        continue
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        check(False, f"SHA256SUMS:{line_number}: path escapes package")
        continue
    if relative in manifest:
        check(False, f"SHA256SUMS:{line_number}: duplicate path {relative}")
    manifest[relative] = expected
    if not path.is_file():
        check(False, f"SHA256SUMS:{line_number}: missing file {relative}")
    else:
        check(sha256(path.read_bytes()) == expected,
              f"SHA256SUMS:{line_number}: digest mismatch {relative}")

for name, frozen in freeze["sources"].items():
    verify_frozen_file(ROOT / name, frozen)
for name, frozen in freeze["inputs"].items():
    verify_frozen_file(ROOT / "inputs" / name, frozen)

check(sha256((ROOT / "test_visual_context_staleness.py").read_bytes())
      == freeze["test_sha256"], "frozen v1 test changed")
check(sha256((ROOT / "Containerfile").read_bytes())
      == freeze["containerfile_sha256"], "frozen Containerfile changed")
check(sha256((ROOT / "inputs/fixture.json").read_bytes())
      == freeze["fixture_sha256"], "frozen fixture changed")
check(sha256((ROOT / "inputs/frame-audit.json").read_bytes())
      == freeze["frame_audit_sha256"], "frozen frame audit changed")

fixture = read_json(ROOT / "inputs/fixture.json")
frame_audit = read_json(ROOT / "inputs/frame-audit.json")
event_rows = [json.loads(line) for line in
              (ROOT / "inputs/events.jsonl").read_text(encoding="utf-8-sig").splitlines()
              if line.strip()]
for sequence, filename in (("2", "002.png"), ("3", "003.png")):
    pair = fixture["pair"][sequence]
    typed = pair["typed_observation"]
    observation = pair["observation"]
    audit_row = frame_audit["frames"][filename]
    with Image.open(ROOT / "inputs" / filename) as image:
        rgb = image.convert("RGB")
        pixel_digest = sha256(rgb.tobytes())
        dimensions = list(rgb.size)
    check(pixel_digest == audit_row["decoded_rgb_sha256"],
          f"{filename}: decoded RGB digest differs from frame audit")
    check(pixel_digest == audit_row["event_frame_rgb_sha256"],
          f"{filename}: decoded RGB digest differs from event digest")
    check(pixel_digest == typed["frame_rgb_sha256"],
          f"{filename}: decoded RGB digest differs from typed observation")
    check(dimensions == audit_row["dimensions"] == typed["frame_size"],
          f"{filename}: decoded dimensions mismatch")
    check(pathlib.PurePosixPath(observation["image"]).name == filename,
          f"{filename}: fixture image name mismatch")
    check(pair["observation"] in event_rows,
          f"{filename}: raw observation row absent")
    check(pair["typed_observation"] in event_rows,
          f"{filename}: raw typed-observation row absent")

run_exit = (ROOT / "results/exit.txt").read_text(encoding="utf-8").strip()
check(run_exit == "0", "retained WSLc run did not exit zero")
transcript = (ROOT / "results/wslc.stdout.txt").read_text(encoding="utf-8-sig")
check("Ran 2 tests" in transcript and
      re.search(r"(?m)^OK\r?$", transcript) is not None,
      "retained WSLc unittest summary missing or failed")

results = read_json(ROOT / "results/result.json")
transcript_records = {"changed": [], "control": []}
for line in transcript.splitlines():
    for arm, prefix in (("changed", "VISUAL_CHANGED="),
                        ("control", "VISUAL_CONTROL=")):
        if line.startswith(prefix):
            try:
                transcript_records[arm].append(json.loads(line[len(prefix):]))
            except json.JSONDecodeError as error:
                check(False, f"{prefix}: invalid JSON record: {error}")
for arm in ("changed", "control"):
    records = transcript_records[arm]
    check(len(records) == 1, f"transcript must contain exactly one {arm} record")
    if len(records) == 1:
        check(records[0] == results[arm],
              f"transcript {arm} record differs from structured result")
    row = results[arm]
    check(row["monitor_invalidation"] is None and row["answer_eligible"] is True,
          f"{arm}: monitor or planner eligibility result invalid")
    check(row["final_status"] == "READY_FOR_FRESH_EXECUTOR_ADMISSION",
          f"{arm}: final status mismatch")
    check(row["executor_admission"] is None and
          row["input_authority_admitted"] is False,
          f"{arm}: authority boundary mismatch")

changed = results["changed"]
control = results["control"]
check(changed["source_frame_rgb_sha256"] != changed["current_frame_rgb_sha256"],
      "changed arm does not contain distinct decoded RGB frames")
check(changed["source_health_ammo"] == changed["current_health_ammo"] == [97, 48],
      "changed arm typed health/ammo differ")
check(changed["source_frame_rgb_sha256"] == control["source_frame_rgb_sha256"] and
      changed["source_health_ammo"] == control["source_health_ammo"],
      "control source does not match changed-arm source")
check(control["source_frame_rgb_sha256"] == control["current_frame_rgb_sha256"],
      "same-frame control hashes differ")
check((ROOT / "results/image_id.txt").read_text(encoding="utf-8").strip()
      == "sha256:4fc7258eb9f2430d573bcbd352fc9851eee6ce96a65ff026274dfb317119bb7b",
      "retained image id mismatch")

if errors:
    print("AUDIT_V2_FAIL")
    print("\n".join(errors))
    sys.exit(1)

print("AUDIT_V2_OK: manifest, frozen inputs/sources, decoded PNG pixels, raw events, "
      "WSLc transcript/result equality, bounded authority, and retained run receipt verified")
