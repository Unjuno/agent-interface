"""Controlled Luna-low runner accepting one to three ordered images."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    node, cli, prompt_file, working, output, instructions, schema, *images = sys.argv[1:]
    if not 1 <= len(images) <= 3: raise ValueError("one to three images required")
    root = Path(output).resolve(); root.mkdir(parents=True, exist_ok=False)
    prompt = Path(prompt_file).read_text(encoding="utf-8")
    (root / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    args = [node, cli, "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral",
            "--sandbox", "read-only", "--skip-git-repo-check", "--json", "--model", "gpt-5.6-luna",
            "-c", 'model_reasoning_effort="low"', "-c",
            "model_instructions_file=" + json.dumps(Path(instructions).resolve().as_posix()),
            "-c", "project_doc_max_bytes=0", "--output-schema", str(Path(schema).resolve()),
            "--disable", "plugins", "--disable", "remote_plugin", "--disable", "shell_snapshot",
            "--disable", "shell_tool", "--disable", "fast_mode", "-C", str(Path(working).resolve())]
    for image in images: args.extend(["--image", str(Path(image).resolve())])
    args.append("-")
    plan = {"args": args, "requested_model": "gpt-5.6-luna", "requested_effort": "low",
            "image_sha256": [sha(path) for path in images], "visible_images_submitted": len(images),
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "instructions_sha256": sha(instructions), "schema_sha256": sha(schema),
            "runner_sha256": sha(__file__), "observed_model_identity": None, "cost": None}
    (root / "plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    started = time.perf_counter_ns()
    with (root / "stderr.txt").open("wb") as errors, (root / "events.jsonl").open("wb") as raw:
        process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors)
        process.stdin.write(prompt.encode()); process.stdin.close()
        for line in process.stdout: raw.write(line); raw.flush()
        code = process.wait()
    result = {"exit_code": code, "started_ns": started, "exited_ns": time.perf_counter_ns(),
              "requested_model": "gpt-5.6-luna", "requested_effort": "low",
              "visible_images_submitted": len(images), "observed_model_identity": None, "cost": None}
    (root / "process.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result)); return code


if __name__ == "__main__": raise SystemExit(main())
