"""Read-only integration intake; never execute the retained GUI runner."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    intake = json.loads((HERE / "intake.json").read_text())
    prefix = intake["capsule_path"] + "/"
    paths = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", "HEAD", "--", prefix],
        cwd=REPO, text=True).splitlines()
    with tempfile.TemporaryDirectory(prefix="click-readiness-intake-") as temp:
        root = Path(temp)
        capsule = root / "capsule"
        for path in paths:
            out = capsule / path[len(prefix):]
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(subprocess.check_output(
                ["git", "show", "HEAD:" + path], cwd=REPO))
        manifest = json.loads((capsule / "CAPSULE.json").read_text())
        require(manifest["archive_sha256"] == intake["capsule_sha256"], "capsule changed")
        unpacked = root / "unpacked"
        restore = subprocess.run([sys.executable, "-B", str(capsule / "unpack.py"),
                                  str(unpacked)], capture_output=True, text=True, check=True)
        require(json.loads(restore.stdout) == json.loads((HERE / "unpack.stdout").read_text()),
                "restore accounting changed")
        for name, digest in intake["unpacked_source_sha256"].items():
            require(hashlib.sha256((unpacked / name).read_bytes()).hexdigest() == digest,
                    "source changed: " + name)
        audit = subprocess.run([sys.executable, "-B", str(unpacked / "audit.py"),
                                str(unpacked)], capture_output=True, text=True, check=True)
        result = json.loads(audit.stdout)
        require(result == json.loads((HERE / "audit.stdout").read_text()), "audit differs")
        require(result["cases"] == 30 and result["errors"] == [], "audit scope")
        rows = []
        for path in sorted((unpacked / "formal-01").glob("batch-*/case-*/row.json")):
            q = json.loads(path.read_text())
            if q["route"] != "CLICK_ENTRY":
                continue
            after = q["snapshots"]["after_activation"]["snapshot"]["ns"]
            before = q["snapshots"]["before_text"]["snapshot"]["ns"]
            require(q["activation_returned_ns"] < after < before < q["text_started_ns"],
                    "observation ordering")
            rows.append({"case": str(path.parent.relative_to(unpacked)),
                         "state": q["state"],
                         "activation_returned_ns": q["activation_returned_ns"],
                         "after_activation_snapshot_ns": after,
                         "before_text_snapshot_ns": before,
                         "text_started_ns": q["text_started_ns"],
                         "activation_to_text_ms": (q["text_started_ns"] - q["activation_returned_ns"]) / 1e6,
                         "final_values": q["snapshots"]["final"]["snapshot"]["values"]})
        require(len(rows) == 9, "click denominator")
        require(rows == json.loads((HERE / "click-boundaries.json").read_text()), "derived boundaries differ")
        runner = (unpacked / "run.py").read_text()
        require(runner.index("snap('after_activation')") < runner.index("snap('before_text')")
                < runner.index("row['text_started_ns']"), "source boundary differs")
        require("root.after(15,finish,command)" in (unpacked / "app.py").read_text(),
                "app scheduling differs")
        print(json.dumps({"status": "PASS", "retained_cases": 30, "click_boundaries": 9,
                          "new_gui_runs": 0, "decision": intake["decision"]}))


if __name__ == "__main__":
    main()
