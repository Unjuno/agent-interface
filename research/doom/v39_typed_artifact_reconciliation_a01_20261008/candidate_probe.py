import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

from PIL import Image

ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = Path(os.environ.get("SOURCE_ROOT", ROOT))
CANDIDATE_ROOT = ROOT / "candidate"
sys.path.insert(0, str(SOURCE_ROOT / "research" / "live_control"))
spec = importlib.util.spec_from_file_location(
    "candidate_doom_typed_observation_v1",
    CANDIDATE_ROOT / "research" / "doom" / "doom_typed_observation_v1.py",
)
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
OUT = ROOT / "results" / "a01" / "RESULT_CANDIDATE.json"
if OUT.exists():
    raise SystemExit("STOP_CANDIDATE_OUTPUT_EXISTS")

class Reader:
    def __init__(self, row):
        self.row = row

    def read(self, observation):
        return copy.deepcopy(self.row)

def main():
    image = Image.new("RGB", (2, 2), (11, 22, 33))
    with tempfile.TemporaryDirectory(prefix="8566-green-") as temp:
        image_path = Path(temp) / "frame.png"
        image.save(image_path)
        binding = {"window": "w1", "geometry": [0, 0, 2, 2]}
        image_hash = candidate.frame_rgb_sha256(image)
        typed = {
            "schema": candidate.SCHEMA, "id": 1, "step": 0,
            "sequence": 1, "capture_ns": 1,
            "pointer_binding": binding, "frame_rgb_sha256": image_hash,
            "signals": {},
        }
        observation = {
            "event": "observation", "exact": True,
            "id": 1, "step": 0, "sequence": 1, "capture_ns": 1,
            "pointer_binding": binding, "image": str(image_path),
        }
        for name, value in (("health", 100), ("ammo", 10)):
            typed["signals"][name] = {
                "status": "observed", "value": value,
                "sequence": 1, "capture_ns": 1,
                "binding": copy.deepcopy(binding),
            }
        base_rows = {
            name: {"status": "observed", "value": value,
                   "sequence": 1, "capture_ns": 1,
                   "binding": copy.deepcopy(binding)}
            for name, value in (("health", 100), ("ammo", 10))
        }
        cases = [("control_exact", None)]
        cases.extend([
            ("id_bool_int_alias", ("id", True, 1)),
            ("step_bool_int_alias", ("step", False, 0)),
            ("sequence_bool_int_alias", ("sequence", True, 1)),
            ("capture_bool_int_alias", ("capture_ns", False, 0)),
            ("binding_nested_bool_int_alias", ("binding", True, 1)),
        ])
        rows = []
        for case, mutation in cases:
            t, o = copy.deepcopy(typed), copy.deepcopy(observation)
            readers = {name: Reader(row) for name, row in base_rows.items()}
            if mutation:
                field, left, right = mutation
                if field == "binding":
                    t["pointer_binding"]["geometry"][0] = left
                    o["pointer_binding"]["geometry"][0] = right
                    for name in t["signals"]:
                        t["signals"][name]["binding"]["geometry"][0] = left
                        readers[name].row["binding"]["geometry"][0] = right
                else:
                    t[field], o[field] = left, right
            result = candidate.reconcile_artifact(t, o, readers)
            rows.append({"case": case, "mutation": mutation,
                         "matched": result["matched"], "checks": result["checks"],
                         "result": result})
    accepted = [row["case"] for row in rows[1:] if row["matched"]]
    payload = {
        "schema": "issue8566-reconcile-alias-a01-candidate-v1",
        "baseline_source_commit": "64c77d54c1a16b63be9084be1b117b628482b377",
        "baseline_source_blob": "930e1c78511b57999a0a2176cb94a31a32d166a8",
        "candidate_source_sha256": hashlib.sha256(
            (CANDIDATE_ROOT / "research/doom/doom_typed_observation_v1.py").read_bytes()
        ).hexdigest(),
        "control_matched": rows[0]["matched"],
        "accepted_aliases": accepted,
        "result": ("PASS_EXACT_IDENTITY" if rows[0]["matched"] and not accepted
                   else "FAIL_CANDIDATE_ALIAS_ACCEPTED" if accepted
                   else "HOLD_CONTROL_REJECTED"),
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    raw = OUT.read_bytes()
    print(json.dumps({"result": payload["result"],
                      "control_matched": payload["control_matched"],
                      "accepted_aliases": accepted,
                      "raw_sha256": hashlib.sha256(raw).hexdigest()},
                     sort_keys=True))

if __name__ == "__main__":
    main()
