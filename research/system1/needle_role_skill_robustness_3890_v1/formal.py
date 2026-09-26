"""Single frozen host orchestration; all training and loading execute in Docker."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

IMAGE = "needle-pilot05:local"
IMAGE_ID = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"
SEEDS = (3792, 3892, 3992, 4092, 4192, 4292, 4392, 4492, 4592, 4692)
LIMITS = ["--pull=never", "--platform", "linux/amd64", "--network", "none",
          "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev,size=64m",
          "--pids-limit", "64", "--memory", "2g", "--cpus", "1"]


def mount(path, target, readonly=False):
    value = f"type=bind,source={Path(path).resolve().as_posix()},target={target}"
    return value + (",readonly" if readonly else "")


def base_docker(source, output, image_id):
    return ["docker", "run", "--rm", *LIMITS,
            "--mount", mount(source, "/src", True),
            "--mount", mount(output, "/out", False),
            "--workdir", "/src", "--entrypoint", "python", image_id, "-B"]


def commands(source, output, seed):
    root = Path(output) / f"seed-{seed}"
    builder = root / "builder"
    return {
        "builder": [*base_docker(source, builder, IMAGE), "runner.py"],
        "loader1": ["docker", "run", "--rm", *LIMITS,
                    "--mount", mount(source, "/src", True),
                    "--mount", mount(builder, "/builder", True),
                    "--mount", mount(root / "load1", "/out", False),
                    "--workdir", "/src", "--entrypoint", "python", IMAGE, "-B",
                    "loader.py", "/builder/skill.json",
                    "/builder/expected.json.gz", "/out/loader.json"],
        "loader2": ["docker", "run", "--rm", *LIMITS,
                    "--mount", mount(source, "/src", True),
                    "--mount", mount(builder, "/builder", True),
                    "--mount", mount(root / "load2", "/out", False),
                    "--workdir", "/src", "--entrypoint", "python", IMAGE, "-B",
                    "loader.py", "/builder/skill.json",
                    "/builder/expected.json.gz", "/out/loader.json"],
    }


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json_new(path, obj):
    with open(path, "x", encoding="utf-8") as f:
        json.dump(obj, f, sort_keys=True, separators=(",", ":"), allow_nan=False)
        f.write("\n")


def invoke(name, argv, cwd, logdir, context):
    started = time.time_ns()
    try:
        result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", check=False)
    except Exception as exc:
        write_json_new(Path(logdir) / f"{name}.STOP.json",
                       {"status": "STOP", "phase": name, **context,
                        "exception": type(exc).__name__, "message": str(exc),
                        "no_retry": True})
        raise
    (Path(logdir) / f"{name}.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (Path(logdir) / f"{name}.stderr.txt").write_text(result.stderr, encoding="utf-8")
    if result.returncode:
        write_json_new(Path(logdir) / f"{name}.STOP.json",
                       {"status": "STOP", "phase": name, **context,
                        "exit_code": result.returncode, "command": argv,
                        "stdout": result.stdout, "stderr": result.stderr,
                        "no_retry": True})
        raise RuntimeError(f"{name} failed; retained typed STOP, no retry")
    return {"name": name, "command": argv, "exit_code": 0,
            "started_ns": started, "finished_ns": time.time_ns(),
            "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    source = Path(args.source).resolve()
    output = Path(args.out).resolve()
    if not source.is_dir() or not output.is_dir() or any(output.iterdir()):
        raise SystemExit("source must exist and formal output must exist and be empty")
    inspect = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", IMAGE],
                             capture_output=True, text=True, check=False)
    observed = inspect.stdout.strip()
    if inspect.returncode or observed != IMAGE_ID:
        write_json_new(output / "STOP.json",
                       {"status": "STOP", "phase": "image_preflight",
                        "expected_image_id": IMAGE_ID, "observed_image_id": observed,
                        "stderr": inspect.stderr, "no_retry": True})
        return 1
    invocations = []
    started_ns = time.time_ns()
    try:
        for seed in SEEDS:
            root = output / f"seed-{seed}"
            root.mkdir()
            for name in ("builder", "load1", "load2"):
                (root / name).mkdir()
            cmd = commands(source, output, seed)
            context = {"seed": seed, "image_id": IMAGE_ID}
            invocations.append(invoke(f"seed-{seed}-builder", cmd["builder"], source, root, context))
            package = root / "builder" / "skill.json"
            (root / "artifact.before-load.sha256").write_text(sha(package) + "\n", encoding="ascii")
            invocations.append(invoke(f"seed-{seed}-loader1", cmd["loader1"], source, root, context))
            invocations.append(invoke(f"seed-{seed}-loader2", cmd["loader2"], source, root, context))
            (root / "artifact.after-load.sha256").write_text(sha(package) + "\n", encoding="ascii")
        write_json_new(output / "FORMAL_INVOCATION.json",
                       {"status": "COMPLETE", "allocation": "needle-role-skill-robustness-3890-v1",
                        "issue": 4479, "image": IMAGE, "image_id": IMAGE_ID,
                        "seeds": list(SEEDS), "started_ns": started_ns,
                        "finished_ns": time.time_ns(), "invocations": invocations,
                        "formal_orchestrations": 1, "retries": 0})
        print(json.dumps({"formal": "COMPLETE", "invocations": len(invocations),
                          "seeds": len(SEEDS)}, sort_keys=True))
        return 0
    except Exception as exc:
        if not (output / "STOP.json").exists():
            write_json_new(output / "STOP.json",
                           {"status": "STOP", "phase": "orchestration",
                            "exception": type(exc).__name__, "message": str(exc),
                            "completed_invocations": invocations, "no_retry": True})
        print(json.dumps({"formal": "STOP", "completed_invocations": len(invocations),
                          "no_retry": True}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

