"""Run the installed host-local codex.exe with the existing evidence envelope."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    # Keep the positional contract of target_handle_model_runner_v2 so callers
    # can select this runner without changing their evidence parser.
    _node, _legacy_cli, prompt_file, working, output, mode, image, instructions, schema = sys.argv[1:]
    if mode not in ("coordinate", "handle"):
        raise ValueError("mode must be coordinate or handle")
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=False)
    prompt = Path(prompt_file).read_text(encoding="utf-8")
    schema = Path(schema).resolve()
    instructions = Path(instructions).resolve()
    image_path = None if image == "-" else Path(image).resolve()
    if mode == "coordinate" and image_path is None:
        raise ValueError("coordinate mode requires an image")
    if mode == "handle" and image_path is not None:
        raise ValueError("handle mode must not receive an image")
    cli = os.environ.get("CODEX_EXE", "codex.exe")
    args = [cli, "exec", "--ignore-user-config", "--ignore-rules",
            "--ephemeral", "--sandbox", "read-only", "--skip-git-repo-check",
            "--json", "--model", "gpt-5.6-luna", "-c",
            'model_reasoning_effort="low"', "-c", "project_doc_max_bytes=0",
            "--output-schema", str(schema)]
    if image_path is not None:
        args.extend(["--image", str(image_path)])
    args.extend(["-C", str(Path(working).resolve()), "-"])
    plan = {"args": args, "mode": mode, "requested_model": "gpt-5.6-luna",
            "requested_effort": "low", "image_sha256": None if image_path is None else sha(image_path),
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "instructions_sha256": sha(instructions), "schema_sha256": sha(schema),
            "runner_sha256": sha(Path(__file__).resolve()),
            "boundary": "host-local-codex-exe", "authority_granted": False}
    (root / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    (root / "plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    started = time.perf_counter_ns()
    with (root / "stderr.txt").open("wb") as errors, (root / "events.jsonl").open("wb") as raw, \
            (root / "arrivals.jsonl").open("w", encoding="utf-8", newline="\n") as arrivals:
        process = subprocess.Popen(args, cwd=str(Path(working).resolve()), stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=errors)
        process.stdin.write(prompt.encode("utf-8")); process.stdin.close()
        sent = time.perf_counter_ns()
        for index, line in enumerate(process.stdout):
            received = time.perf_counter_ns(); raw.write(line); raw.flush()
            arrivals.write(json.dumps({"line": index, "received_ns": received,
                "sha256": hashlib.sha256(line).hexdigest(), "bytes": len(line)} ) + "\n"); arrivals.flush()
        code = process.wait()
    result = {"exit_code": code, "started_ns": started, "stdin_closed_ns": sent,
              "exited_ns": time.perf_counter_ns(), "requested_model": "gpt-5.6-luna",
              "requested_effort": "low", "mode": mode, "boundary": "host-local-codex-exe",
              "authority_granted": False}
    (root / "process.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
