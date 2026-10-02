import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    if len(sys.argv) != 7:
        raise SystemExit("usage: run_controls.py AUDITOR FREEZE DATA RAW MODEL OUTPUT")
    auditor, freeze, data_path, raw_path, model, output = map(Path, sys.argv[1:])
    original_raw = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    original_data = json.loads(data_path.read_text(encoding="utf-8"))
    mutations = ("change_seed", "drop_row", "inject_candidate", "alter_constrained_text",
                 "alter_prompt_tokens", "inject_effect", "corrupt_input_bytes", "inject_source_hash")
    results = []
    for mutation in mutations:
        with tempfile.TemporaryDirectory(prefix="qwen-grammar-control-", dir="/tmp") as temp:
            work = Path(temp)
            raw = copy.deepcopy(original_raw)
            data = copy.deepcopy(original_data)
            raw_out = work / "RAW.jsonl"
            data_out = work / "DATASET.json"
            if mutation == "change_seed":
                raw[0]["seed"] += 1
            elif mutation == "drop_row":
                raw.pop()
            elif mutation == "inject_candidate":
                data["rows"][0]["candidates"].append('{"op":"toggle","target":"forged"}')
            elif mutation == "alter_constrained_text":
                raw[1]["constrained"]["raw_text"] = '{"op":"save"}'
            elif mutation == "alter_prompt_tokens":
                raw[1]["prompt_input_ids"][0] += 1
            elif mutation == "inject_effect":
                raw[1]["constrained"]["effect"] = {"changed": True, "kind": "forged"}
            elif mutation == "corrupt_input_bytes":
                data_out.write_bytes(data_path.read_bytes() + b"x")
            elif mutation == "inject_source_hash":
                raw[0]["source_sha256"]["run_pair.py"] = "0" * 64
            if mutation != "corrupt_input_bytes":
                data_out.write_text(json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
            raw_out.write_text("".join(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n" for obj in raw), encoding="utf-8")
            audit_out = work / "audit"
            command = [sys.executable, str(auditor), "--freeze", str(freeze), "--data", str(data_out),
                       "--raw", str(raw_out), "--model", str(model), "--out", str(audit_out)]
            process = subprocess.run(command, capture_output=True, text=True)
            results.append({"mutation": mutation, "rejected": process.returncode != 0, "exit": process.returncode})
    summary = {"schema": "qwen-intent-grammar-corruption-controls-v2", "controls": results,
               "rejected": sum(item["rejected"] for item in results), "total": len(results),
               "pass_all": all(item["rejected"] for item in results)}
    output.mkdir(parents=True, exist_ok=True)
    (output / "CONTROL_RESULTS.json").write_text(json.dumps(summary, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    raise SystemExit(0 if summary["pass_all"] else 2)


if __name__ == "__main__":
    main()
