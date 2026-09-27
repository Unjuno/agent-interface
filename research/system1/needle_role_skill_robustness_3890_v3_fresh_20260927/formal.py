"""Single frozen orchestrator for Issue #4580; never retries a container."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

SEEDS = [2026092700, 2026092800, 2026092900, 2026093000, 2026093100,
         2026093200, 2026093300, 2026093400, 2026093500, 2026093600]
IMAGE = "needle-pilot05:local"
IMAGE_ID = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"
UPSTREAM = {
    "runner.py": "a0e99b991a8a3ab9b2f4b6f4f22f7c705989447ce64a14738026fcd763b55abb",
    "loader.py": "5ff6df91ea3929f68fe77ccd6156bdb1310d0fec86088489d8b99905a7c5854f",
    "audit.py": "4e53e241aa115202ce9ca2ce3a5b3df76599b80ad03290a61594bd6b0e35c3a0",
    "PREREGISTRATION.md": "b2ccbac02e0d759c662b955fb34127310ea87d2cbdfe72d91b356a750ffd3c7a",
}


class Stop(Exception):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def effective_source(path, expected):
    raw = Path(path).read_bytes()
    candidates = (raw, raw.rstrip(b"\n"), raw.rstrip(b"\n") + b"\n")
    for candidate in candidates:
        if sha(candidate) == expected:
            return candidate
    raise Stop("SOURCE_HASH_MISMATCH:" + str(path))


def validate_output(seed, outdir):
    if type(seed) is not int or seed not in SEEDS:
        raise Stop("NEEDLE_SEED_MISSING_OR_INVALID")
    path = Path(outdir).resolve()
    if path.name != "builder" or path.parent.name != f"seed-{seed}" or not path.is_dir():
        raise Stop("NEEDLE_OUTPUT_NOT_UNIQUE_SEED_DIRECTORY")
    if any(path.iterdir()):
        raise Stop("NEEDLE_OUTPUT_NOT_EMPTY")
    return path


def validate_bindings(seed_value, output_value):
    if seed_value is None or output_value is None:
        raise Stop("NEEDLE_SEED_OR_NEEDLE_OUTPUT_MISSING")
    try:
        seed = int(seed_value)
    except (TypeError, ValueError):
        raise Stop("NEEDLE_SEED_INVALID")
    if seed not in SEEDS or output_value != "/out":
        raise Stop("NEEDLE_SEED_OR_NEEDLE_OUTPUT_INVALID")
    return seed


def docker_common(image_id):
    if image_id != IMAGE_ID:
        raise Stop("PINNED_IMAGE_ID_MISMATCH")
    return ["docker", "run", "--rm", "--network", "none", "--read-only",
            "--cpus=1", "--memory=2g", "--pids-limit=64",
            "--tmpfs", "/tmp:rw,nosuid,nodev,size=256m"]


def source_bootstrap(source_bytes, argv=None):
    digest = sha(source_bytes)
    set_argv = "" if argv is None else "sys.argv=" + repr(argv) + ";"
    return ("import hashlib,sys;raw=bytes.fromhex('" + source_bytes.hex() + "');"
            "assert hashlib.sha256(raw).hexdigest()=='" + digest + "';" + set_argv +
            "exec(compile(raw,'<pinned-source>','exec'),{'__name__':'__main__'})")


def builder_argv(seed, outdir, source_dir, source_bytes, image_id):
    if validate_bindings(str(seed), "/out") != seed:
        raise Stop("NEEDLE_SEED_BINDING_MISMATCH")
    out = validate_output(seed, outdir)
    cmd = docker_common(image_id) + ["-e", f"NEEDLE_SEED={seed}", "-e", "NEEDLE_OUTPUT=/out",
          "-e", "HOME=/tmp", "-v", f"{Path(source_dir).resolve()}:/src:ro",
          "-v", f"{out}:/out:rw", "--entrypoint", "python", IMAGE, "-c",
          source_bootstrap(source_bytes)]
    return cmd


def loader_argv(source_dir, source_bytes, package, expected, outdir, image_id):
    output = Path(outdir).resolve()
    if output.name not in ("load1", "load2") or not output.is_dir() or any(output.iterdir()):
        raise Stop("LOADER_OUTPUT_NOT_EMPTY_OR_UNIQUE")
    code = source_bootstrap(source_bytes, ["loader.py", "/package/skill.json", "/expected.json", "/out/loader.json"])
    cmd = docker_common(image_id) + ["-e", "HOME=/tmp",
          "-v", f"{Path(source_dir).resolve()}:/src:ro",
          "-v", f"{Path(package).resolve()}:/package/skill.json:ro",
          "-v", f"{Path(expected).resolve()}:/expected.json:ro",
          "-v", f"{output}:/out:rw", "--entrypoint", "python", IMAGE,
          "-c", code]
    return cmd


def run_once(cmd, log_path):
    start = time.monotonic_ns()
    result = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    elapsed = (time.monotonic_ns() - start) / 1e9
    Path(log_path).write_bytes(b"STDOUT\n" + result.stdout + b"\nSTDERR\n" + result.stderr)
    return {"returncode": result.returncode, "elapsed_s": elapsed,
            "stdout_sha256": sha(result.stdout), "stderr_sha256": sha(result.stderr),
            "stdout": result.stdout.decode("utf-8", "replace"),
            "stderr": result.stderr.decode("utf-8", "replace")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--freeze", required=True, type=Path)
    ap.add_argument("--image-id", required=True)
    args = ap.parse_args()
    root = args.output.resolve()
    if root.exists() and any(root.iterdir()):
        raise Stop("FORMAL_OUTPUT_ROOT_NOT_EMPTY")
    root.mkdir(parents=True, exist_ok=True)
    source_dir = args.source.resolve()
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    project = source_dir.parent
    for rel, expected in freeze["source_sha256"].items():
        if rel.startswith("source/") and Path(rel).name in UPSTREAM:
            effective_source(project / rel, expected)
            continue
        if sha((project / rel).read_bytes()) != expected:
            raise Stop("FROZEN_SOURCE_HASH_MISMATCH:" + rel)
    pinned = {name: effective_source(source_dir / name, digest) for name, digest in UPSTREAM.items()}
    parent_freeze = (source_dir / "FREEZE.json").read_bytes()
    if not any(git_blob_sha(candidate) == freeze["parent_freeze_blob_sha1"]
               for candidate in (parent_freeze, parent_freeze.rstrip(b"\n"), parent_freeze.rstrip(b"\n") + b"\n")):
        raise Stop("PARENT_FREEZE_BLOB_MISMATCH")
    runner, loader = pinned["runner.py"], pinned["loader.py"]
    image = subprocess.run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"],
                          capture_output=True, text=True, check=False)
    if image.returncode != 0 or image.stdout.strip() != args.image_id:
        raise Stop("PINNED_IMAGE_NOT_AVAILABLE_OR_ID_MISMATCH")
    docker_common(args.image_id)
    records = []
    for seed in SEEDS:
        sd = root / f"seed-{seed}"
        sd.mkdir()
        builder = sd / "builder"
        builder.mkdir()
        try:
            cmd = builder_argv(seed, builder, source_dir, runner, args.image_id)
            build = run_once(cmd, sd / "builder.log")
            rec = {"seed": seed, "builder": build, "loaders": []}
            if build["returncode"] == 125:
                rec["typed_stop"] = "DOCKER_RUNTIME_OR_IMAGE_STOP"
                records.append(rec)
                break
            if build["returncode"] == 0 and (builder / "skill.json").is_file() and (builder / "expected.json").is_file():
                package, expected = builder / "skill.json", builder / "expected.json"
                before = sha(package.read_bytes())
                for name in ("load1", "load2"):
                    dest = sd / name
                    dest.mkdir()
                    result = run_once(loader_argv(source_dir, loader, package, expected, dest,
                                                   args.image_id), sd / f"{name}.log")
                    result["name"] = name
                    result["loader_json_exists"] = (dest / "loader.json").is_file()
                    result["package_sha256_after"] = sha(package.read_bytes())
                    rec["loaders"].append(result)
                rec["package_sha256_before"] = before
                rec["package_sha256_after_all_loaders"] = sha(package.read_bytes())
            records.append(rec)
        except Stop as exc:
            records.append({"seed": seed, "typed_stop": str(exc), "builder": None, "loaders": []})
    report = {"schema": "needle-role-skill-robustness-v3-formal-run-v1",
              "allocation": "needle-role-skill-robustness-3890-v3-fresh-20260927",
              "issue": 4580, "image": IMAGE, "image_id": args.image_id,
              "freeze_sha256": sha(args.freeze.read_bytes()),
              "source_sha256": freeze["source_sha256"],
              "formal_orchestrations": 1, "retries": 0, "tuning": 0,
              "seeds": records, "created_unix_ns": time.time_ns()}
    path = root / "FORMAL_RUN.json"
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, sort_keys=True, separators=(",", ":"), allow_nan=False)
        f.write("\n")
    print(json.dumps({"seeds": len(records), "successful_builders": sum(r.get("builder", {}).get("returncode") == 0 for r in records),
                      "retries": 0, "report": str(path)}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Stop as exc:
        print(json.dumps({"schema": "needle-role-skill-typed-stop-v1", "status": "STOP", "reason": str(exc), "formal_runs": 0}, sort_keys=True))
        raise SystemExit(2)

