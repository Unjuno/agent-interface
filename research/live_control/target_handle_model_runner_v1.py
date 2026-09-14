"""Explicit Luna-low runner for image-coordinate or text-handle decisions."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    node, cli, prompt_file, working, output, mode, image = sys.argv[1:]
    if mode not in ("coordinate", "handle"):
        raise ValueError("mode must be coordinate or handle")
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=False)
    prompt = Path(prompt_file).read_text(encoding="utf-8")
    (root / "prompt.txt").write_text(prompt, encoding="utf-8")
    args = [node, cli, "exec", "--ignore-user-config", "--ephemeral",
            "--sandbox", "read-only", "--skip-git-repo-check", "--json",
            "--model", "gpt-5.6-luna", "-c", 'model_reasoning_effort="low"',
            "--disable", "plugins", "--disable", "remote_plugin",
            "--disable", "shell_snapshot", "--disable", "shell_tool",
            "--disable", "fast_mode", "-C", str(Path(working).resolve())]
    image_path = None
    if mode == "coordinate":
        image_path = Path(image).resolve()
        args.extend(["-i", str(image_path)])
    elif image != "-":
        raise ValueError("handle mode must not receive an image")
    args.append("-")
    plan = {"args": args, "mode": mode, "requested_model": "gpt-5.6-luna",
            "requested_effort": "low", "image_sha256": None if image_path is None else
                hashlib.sha256(image_path.read_bytes()).hexdigest(),
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "clock": "perf_counter_ns in runner process; local arrival only",
            "observed_model_identity": None, "cost": None}
    (root / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    started = time.perf_counter_ns()
    with (root / "stderr.txt").open("wb") as errors, \
            (root / "events.jsonl").open("wb") as raw, \
            (root / "arrivals.jsonl").open("w") as arrivals:
        process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=errors)
        process.stdin.write(prompt.encode("utf-8"))
        process.stdin.close()
        sent = time.perf_counter_ns()
        for index, line in enumerate(process.stdout):
            received = time.perf_counter_ns()
            raw.write(line)
            arrivals.write(json.dumps({"line": index, "received_ns": received,
                "sha256": hashlib.sha256(line).hexdigest(), "bytes": len(line)}) + "\n")
            raw.flush()
            arrivals.flush()
        code = process.wait()
    result = {"exit_code": code, "started_ns": started, "stdin_closed_ns": sent,
              "exited_ns": time.perf_counter_ns(), "requested_model": "gpt-5.6-luna",
              "requested_effort": "low", "mode": mode,
              "observed_model_identity": None, "cost": None}
    (root / "process.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
