"""Audit the cropped pre-formal MAP01 inference-overlap result."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/map01-overlap-crop-luna-01"

def read(path): return json.loads(path.read_text())
events = [json.loads(line) for line in (ROOT / "runtime/events.jsonl").read_text().splitlines()]
report = read(ROOT / "report.json")
decision = report["decisions"][0]
accepted = next(row for row in events if row["event"] == "accepted" and row.get("id") == "cover-0")
terminal = next(row for row in events if row["event"] == "terminal" and row.get("id") == "cover-0")
plan = next(row for row in events if row["event"] == "terminal" and row.get("id") == "plan-0")
assert accepted["accepted_ns"] <= decision["controller_model_started_ns"]
assert decision["controller_model_ended_ns"] <= terminal["terminal_ns"]
assert terminal["status"] == "cancelled" and terminal["release"]["verified"] is True
assert plan["status"] == "completed" and plan["release"]["verified"] is True
assert decision["usage"]["input_tokens"] == 8366
assert report["score"]["map_exit"] is False and report["score"]["player_dead"] is False
image = ROOT / "decision-0/game-window.png"
assert hashlib.sha256(image.read_bytes()).hexdigest() == decision["model_image_sha256"]
result = {"audit_passed": True, "model_fully_overlapped_by_cover": True,
          "input_tokens": 8366, "uncropped_reference_input_tokens": 9158,
          "scoped_reduction_percent": round((1-8366/9158)*100, 3),
          "cover_release_verified": True, "plan_release_verified": True,
          "alive_at_finish": True, "map_clear_claimed": False}
(ROOT / "audit.json").write_text(json.dumps(result, indent=2)+"\n")
print(json.dumps(result, indent=2))
