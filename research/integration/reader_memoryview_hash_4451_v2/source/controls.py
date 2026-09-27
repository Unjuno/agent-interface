"""Independent corruption controls for the raw-result auditor."""

import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STUDY = ROOT.parent


def main():
    freeze = json.loads((STUDY / "FREEZE.json").read_text(encoding="utf-8"))
    image_id = freeze["container_image_id"]
    with tempfile.TemporaryDirectory(prefix="reader-memoryview-controls-") as temp:
        base = Path(temp) / "base"
        base.mkdir()
        shutil.copy2(STUDY / "FREEZE.json", base / "FREEZE.json")
        shutil.copy2(STUDY / "ENVIRONMENT.json", base / "ENVIRONMENT.json")
        shutil.copytree(ROOT, base / "source")
        out = Path(temp) / "out"
        ok = subprocess.run(
            [sys.executable, "-B", str(base / "source" / "supervise.py"), "--phase", "construction",
             "--out", str(out), "--image-id", image_id],
            cwd=base / "source", capture_output=True, text=True, timeout=30,
        )
        if ok.returncode:
            raise RuntimeError(ok.stdout + ok.stderr)
        raw_path = out / "RAW.json"
        original = json.loads(raw_path.read_text(encoding="utf-8"))
        def corrupt_worker_stdout(raw):
            row = json.loads(raw["resource"][0]["stdout"])
            row["source_sha256"] = "0" * 64
            row["input_sha256_before"] = "0" * 64
            row["result"]["authority"] = "write"
            raw["resource"][0]["stdout"] = json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"

        mutations = {
            "drop_resource": lambda r: r["resource"].pop(),
            "duplicate_resource": lambda r: r["resource"].append(copy.deepcopy(r["resource"][0])),
            "arm_identity": lambda r: r["resource"][0].__setitem__("arm", "candidate"),
            "cursor_identity": lambda r: r["resource"][0].__setitem__("cursor_records", -1),
            "source_row": corrupt_worker_stdout,
            "result_authority": corrupt_worker_stdout,
            "input_hash": corrupt_worker_stdout,
            "exit_code": lambda r: r["resource"][0].__setitem__("exit", 7),
            "corpus_hash": lambda r: r.__setitem__("corpus_sha256", "0" * 64),
            "contract_data": lambda r: r["contracts"][0].__setitem__("status", "PASS"),
            "journal_hash": lambda r: r.__setitem__("journal_sha256", "0" * 64),
            "journal_row": lambda r: r["journal"].pop(),
            "source_map": lambda r: r["source_sha256"].__setitem__("worker.py", "0" * 64),
            "environment_image": lambda r: r["environment"].__setitem__("image_id", "sha256:" + "0" * 64),
            "worker_log_hash": lambda r: r["resource"][0].__setitem__("stdout_sha256", "0" * 64),
            "freeze_hash": lambda r: r.__setitem__("freeze_sha256", "0" * 64),
        }
        outcomes = {}
        for name, mutate in mutations.items():
            trial = copy.deepcopy(original)
            try:
                mutate(trial)
            except (IndexError, KeyError):
                trial["resource"] = []
            raw_path.write_text(json.dumps(trial, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            audit = subprocess.run(
                [sys.executable, "-B", str(base / "source" / "audit.py"), str(raw_path)],
                cwd=base / "source", capture_output=True, text=True, timeout=30,
            )
            outcomes[name] = audit.returncode != 0
        rejected = sum(outcomes.values())
        print(json.dumps({"status": "PASS_CORRUPTION_CONTROLS" if rejected == len(mutations) else "FAIL_CORRUPTION_CONTROLS",
                          "rejected": rejected, "total": len(mutations), "outcomes": outcomes}, sort_keys=True))
        if rejected != len(mutations):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
