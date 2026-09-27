import copy
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path("/out")
SOURCE = Path("/src/run.py")
RESULT_PATH = ROOT / "formal-result.json"
RAW_PATH = ROOT / "raw_frames_and_weights.npz"
EXPECTED_SOURCE_SHA256 = "f42ce1c014a5c6a50dd13efdbed083b63fce284386665254559b280e9ff87e75"
EXPECTED_COLORS = {"base-target": "#22cc44", "base-other": "#2244cc",
                   "shift-target": "#55dd66", "shift-other": "#5566dd"}
EXPECTED_SEEDS = [40, 41, 42, 43, 44]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def valid(r, a, source_sha):
    if source_sha != EXPECTED_SOURCE_SHA256:
        return False
    if (r.get("label") != "FIXTURE ITEM" or r.get("layout", [None])[0] != "FIXTURE ITEM"
            or r.get("colors") != EXPECTED_COLORS or r.get("seeds") != EXPECTED_SEEDS):
        return False
    if r.get("base_capture_count") != 16 or r.get("input_dims") != 172800:
        return False
    if r.get("gradient_steps") != 100 or r.get("learning_rate") != 0.3:
        return False
    if set(a.files) != {"base_target", "base_other", "shift_target", "shift_other", "weights", "biases"}:
        return False
    if a["base_target"].shape != (8, 180, 320, 3) or a["base_other"].shape != (8, 180, 320, 3):
        return False
    if a["shift_target"].shape != (180, 320, 3) or a["shift_other"].shape != (180, 320, 3):
        return False
    if a["weights"].shape != (5, 172800) or a["biases"].shape != (5,):
        return False
    if not np.isfinite(a["weights"]).all() or not np.isfinite(a["biases"]).all():
        return False
    hashes = r.get("base_frame_hashes", {})
    for name, array in (("base-target", a["base_target"]), ("base-other", a["base_other"])):
        actual = [sha(frame.tobytes()) for frame in array]
        if actual != hashes.get(name) or len(set(actual)) != 1:
            return False
    for name, array in (("shift-target", a["shift_target"]), ("shift-other", a["shift_other"])):
        actual = [sha(array.tobytes())]
        if actual != hashes.get(name):
            return False
    if len(set(hashes.get("base-target", [])[:1] + hashes.get("base-other", [])[:1])) != 2:
        return False
    if sha(a["shift_target"].tobytes()) == sha(a["shift_other"].tobytes()):
        return False
    rows = r.get("rows", [])
    if len(rows) != 10 or {(x.get("seed"), x.get("case")) for x in rows} != {
            (s, c) for s in EXPECTED_SEEDS for c in ("shift-target", "shift-other")}:
        return False
    by_key = {(x["seed"], x["case"]): x for x in rows}
    correct_count = 0
    threshold_count = 0
    for seed_idx, seed in enumerate(EXPECTED_SEEDS):
        for case, y, frame in (("shift-target", 1, a["shift_target"]),
                               ("shift-other", 0, a["shift_other"])):
            x = frame.reshape(-1).astype(np.float32) / 255.0
            z = float(np.clip(x @ a["weights"][seed_idx] + a["biases"][seed_idx], -30.0, 30.0))
            prob = 1.0 / (1.0 + np.exp(-z))
            row = by_key[(seed, case)]
            if abs(prob - row.get("p_target", -1.0)) > 1e-6:
                return False
            if bool(prob >= 0.5) != bool(y) or row.get("correct") is not True:
                return False
            if row.get("threshold_pass") is not (bool(prob >= 0.75) if y else bool(prob < 0.5)):
                return False
            if row.get("frame_sha256") != sha(frame.tobytes()):
                return False
            correct_count += int(row["correct"])
            threshold_count += int(row["threshold_pass"])
    return (correct_count == 10 and r.get("accuracy") == 1.0
            and threshold_count == r.get("threshold_pass_count") == 10
            and r.get("all_finite") is True)


def main():
    source_sha = sha(SOURCE.read_bytes())
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    with np.load(RAW_PATH, allow_pickle=False) as raw:
        arrays = {k: raw[k].copy() for k in raw.files}
    class Raw:
        files = list(arrays)
        def __getitem__(self, key):
            return arrays[key]

    errors = [] if valid(result, Raw(), source_sha) else ["formal_raw_integrity"]
    mutations = {}
    def mutate(name, fn):
        rr = copy.deepcopy(result)
        aa = {k: v.copy() for k, v in arrays.items()}
        fn(rr, aa)
        class Changed:
            files = list(aa)
            def __getitem__(self, key):
                return aa[key]
        mutations[name] = not valid(rr, Changed(), source_sha)

    mutate("label", lambda r, a: r.__setitem__("label", "TARGET"))
    mutate("capture_count", lambda r, a: r.__setitem__("base_capture_count", 15))
    mutate("color_map", lambda r, a: r["colors"].__setitem__("shift-target", "#ffffff"))
    mutate("prediction", lambda r, a: r["rows"][0].__setitem__("p_target", 0.0))
    mutate("class", lambda r, a: r["rows"][0].__setitem__("case", "shift-other"))
    mutate("frame_hash", lambda r, a: r["rows"][0].__setitem__("frame_sha256", "0" * 64))
    mutate("weights", lambda r, a: a["weights"].__setitem__((0, 0), a["weights"][0, 0] + 1.0))
    mutate("threshold_count", lambda r, a: r.__setitem__("threshold_pass_count", 9))
    mutate("seed", lambda r, a: r["seeds"].__setitem__(0, 99))
    mutate("finite", lambda r, a: a["weights"].__setitem__((0, 0), float("nan")))
    audit = {"passed": not errors and all(mutations.values()), "errors": errors,
             "checks": 20, "corruption_controls": mutations,
             "rejected_controls": sum(mutations.values()),
             "source_sha256": source_sha, "result_sha256": sha(RESULT_PATH.read_bytes()),
             "raw_npz_sha256": sha(RAW_PATH.read_bytes())}
    (ROOT / "independent-audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()



