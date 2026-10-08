"""Create a path-sanitized, append-only public record from a frozen probe run."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.run_dir.resolve(strict=True)
    raw_path = root / "PROBE_RESULT.json"
    public_path = root / "PUBLIC_RESULT.json"
    if public_path.exists():
        raise SystemExit("STOP_PUBLIC_RESULT_EXISTS")

    data = json.loads(raw_path.read_text(encoding="utf-8"))
    result = copy.deepcopy(data)
    result["raw_result_sha256"] = sha256(raw_path.read_bytes())
    result["retained_output_sha256"] = {}
    for name in ("control.trace-cases.json", "control.verification.json",
                 "control.audit.json", "closed.trace-cases.json",
                 "closed.verification.json"):
        path = root / name
        result["retained_output_sha256"][name] = sha256(path.read_bytes())

    for run in result["runs"].values():
        for key in ("verify", "audit"):
            invocation = run.get(key)
            if not invocation:
                continue
            invocation["argv"] = [
                "$PYTHON" if "python.exe" in arg.lower() else
                "$SOURCE/" + Path(arg).name if arg.lower().endswith((".py", ".json")) and "o2-w2-independent-audit-20260928" in arg.lower() else
                "$OUT/" + Path(arg).name if "o2-w2-lease-close-order-probe-20260928" in arg.lower() else arg
                for arg in invocation["argv"]
            ]
            for stream in ("stdout", "stderr"):
                text = invocation.get(stream, "")
                lines = []
                for line in text.splitlines():
                    if "o2-w2-independent-audit-20260928" in line.lower():
                        line = "$SOURCE/" + line.rsplit("\\", 1)[-1]
                    if "o2-w2-lease-close-order-probe-20260928" in line.lower():
                        line = "$OUT/" + line.rsplit("\\", 1)[-1]
                    if "python312\\python.exe" in line.lower():
                        line = line.replace(line, "$PYTHON")
                    lines.append(line)
                invocation[stream] = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    result["runner_argv"] = [
        "python probe_lease_close_order.py --source-dir $SOURCE --output-dir $OUT"
    ]
    result["audit_failure_stderr_sha256"] = sha256(
        data["runs"]["closed"]["audit"]["stderr"].encode("utf-8")
    )
    public_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"public_result": public_path.name,
                      "sha256": sha256(public_path.read_bytes()),
                      "paths_sanitized": True}, indent=2))


if __name__ == "__main__":
    main()
