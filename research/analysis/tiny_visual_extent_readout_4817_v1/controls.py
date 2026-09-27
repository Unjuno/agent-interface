from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main(raw_path, inputs_path, weights_path, initial_path, source_dir):
    raw_original = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    source_dir = Path(source_dir)
    mutations = (
        "alter_logit", "drop_center", "change_allocation", "change_seed", "change_step_count",
        "negative_fit_time", "change_source_hash", "corrupt_input_bytes",
    )
    results = []
    for mutation in mutations:
        with tempfile.TemporaryDirectory(prefix="extent-audit-control-") as tmp:
            tmp = Path(tmp)
            raw = copy.deepcopy(raw_original)
            ip = tmp / "INPUTS.npz"; wp = tmp / "WEIGHTS.npz"; initp = tmp / "INITIAL_WEIGHTS.npz"
            shutil.copy2(inputs_path, ip); shutil.copy2(weights_path, wp); shutil.copy2(initial_path, initp)
            if mutation == "alter_logit": raw["logits"]["max_mean"]["held_0"][0] += 0.01
            elif mutation == "drop_center": raw["logits"]["max_mean"].pop("held_7")
            elif mutation == "change_allocation": raw["allocation"] = "wrong"
            elif mutation == "change_seed": raw["data_seed"] += 1
            elif mutation == "change_step_count": raw["steps"] -= 1
            elif mutation == "negative_fit_time": raw["fit_seconds"]["max_mean"] = -1
            elif mutation == "change_source_hash": raw["source_sha256"]["models.py"] = "0" * 64
            elif mutation == "corrupt_input_bytes": ip.write_bytes(ip.read_bytes() + b"x")
            rp = tmp / "RAW.json"; rp.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            ap = tmp / "AUDIT.json"
            cp = subprocess.run([sys.executable, str(Path(__file__).with_name("audit.py")), str(rp), str(ip), str(wp), str(initp), str(source_dir), str(ap)], capture_output=True, text=True)
            results.append({"mutation": mutation, "rejected": cp.returncode != 0})
    count = sum(row["rejected"] for row in results)
    out = {"controls": results, "rejected": count, "total": len(results), "pass": count == len(results)}
    print(json.dumps(out, sort_keys=True))
    return 0 if out["pass"] else 2


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise SystemExit("usage: controls.py RAW INPUTS WEIGHTS INITIAL_WEIGHTS SOURCE_DIR")
    raise SystemExit(main(*sys.argv[1:]))

