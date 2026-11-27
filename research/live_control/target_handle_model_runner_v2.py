"""Controlled-context Luna runner for coordinate versus target-handle actions."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse_runner_arguments(argv):
    if len(argv) not in (9, 10):
        raise ValueError("expected nine runner arguments and optional model")
    model = argv[9] if len(argv) == 10 else "gpt-5.6-luna"
    if (not isinstance(model, str) or not model or not model.isascii()
            or not model[0].isalnum() or any(not (c.isalnum() or c in "-._:/") for c in model)):
        raise ValueError("invalid model identifier")
    return argv[:9], model


def main():
    args, model = parse_runner_arguments(sys.argv[1:])
    node, cli, prompt_file, working, output, mode, image, instructions, schema = args
    if node == "--native-codex-exe":
        executable = Path(cli)
        if not executable.is_absolute() or executable.suffix.lower() != ".exe":
            raise ValueError("native Codex executable must be an absolute Windows .exe path")
        prefix = [str(executable)]
    else:
        prefix = [node, cli]
    if mode not in ("coordinate", "handle"):
        raise ValueError("mode must be coordinate or handle")
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=False)
    prompt = Path(prompt_file).read_text(encoding="utf-8")
    (root / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    args = [*prefix, "exec", "--ignore-user-config", "--ignore-rules",
            "--ephemeral", "--sandbox", "read-only", "--skip-git-repo-check",
            "--json", "--model", model, "-c",
            'model_reasoning_effort="low"', "-c",
            "model_instructions_file=" + json.dumps(Path(instructions).resolve().as_posix()),
            "-c", "project_doc_max_bytes=0", "--output-schema",
            str(Path(schema).resolve()), "--disable", "plugins", "--disable",
            "remote_plugin", "--disable", "shell_snapshot", "--disable",
            "shell_tool", "--disable", "fast_mode", "-C",
            str(Path(working).resolve())]
    image_path = None
    if mode == "coordinate":
        image_path = Path(image).resolve()
        args.extend(["-i", str(image_path)])
    elif image != "-":
        raise ValueError("handle mode must not receive an image")
    args.append("-")
    plan = {
        "args": args,
        "mode": mode,
        "requested_model": model,
        "requested_effort": "low",
        "image_sha256": None if image_path is None else sha(image_path),
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "instructions_sha256": sha(instructions),
        "schema_sha256": sha(schema),
        "runner_sha256": sha(__file__),
        "clock": "perf_counter_ns in runner process; local arrival only",
        "observed_model_identity": None,
        "cost": None,
    }
    (root / "plan.json").write_text(json.dumps(plan, indent=2) + "\n",
                                    encoding="utf-8", newline="\n")
    started = time.perf_counter_ns()
    with (root / "stderr.txt").open("wb") as errors, \
            (root / "events.jsonl").open("wb") as raw, \
            (root / "arrivals.jsonl").open("w", encoding="utf-8", newline="\n") as arrivals:
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
              "exited_ns": time.perf_counter_ns(), "requested_model": model,
              "requested_effort": "low", "mode": mode,
              "observed_model_identity": None, "cost": None}
    (root / "process.json").write_text(json.dumps(result, indent=2) + "\n",
                                       encoding="utf-8", newline="\n")
    print(json.dumps(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
