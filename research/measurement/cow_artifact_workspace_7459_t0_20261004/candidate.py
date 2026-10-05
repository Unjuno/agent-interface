#!/usr/bin/env python3
"""Drive one disposable Docker-managed COW-layer method experiment."""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "raw"
IMAGE = "local/cow-7459-t0:20261004"
PREFIX = "cow7459t0"


def run(args, *, check=True):
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if check and p.returncode:
        raise RuntimeError(f"exit={p.returncode}: {' '.join(args)}\n{p.stdout}")
    return {"argv": args, "exit": p.returncode, "output": p.stdout}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(131072), b""):
            h.update(b)
    return h.hexdigest()


def inventory(path):
    return {str(p.relative_to(path)): sha(p) for p in sorted(path.rglob("*")) if p.is_file()}


def main():
    if OUT.exists() and any(p.name != "freeze.json" for p in OUT.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    freeze_path = OUT / "freeze.json"
    if not freeze_path.is_file():
        raise SystemExit("STOP_NO_SOURCE_FREEZE")
    OUT.mkdir(parents=True, exist_ok=True)
    source = {str(p.relative_to(ROOT)): sha(p) for p in sorted(ROOT.rglob("*"))
              if p.is_file() and "raw" not in p.parts}
    freeze = json.loads(freeze_path.read_text())
    if freeze.get("files_sha256") != source or freeze.get("repository_head") != run(["git", "-C", str(ROOT.parents[2]), "rev-parse", "HEAD"])["output"].strip():
        raise SystemExit("STOP_SOURCE_OR_MAIN_DRIFT")
    stale_image = run(["docker", "image", "inspect", IMAGE], check=False)
    if stale_image["exit"] == 0:
        raise SystemExit("STOP_IMAGE_TAG_OCCUPIED")
    record = {
        "schema": "cow-7459-t0-candidate-v1",
        "source_sha256": source, "freeze_sha256": sha(freeze_path), "freeze": freeze,
        "docker_version": run(["docker", "version", "--format", "{{.Client.Version}}/{{.Server.Version}}"]),
        "image_inspect": run(["docker", "image", "inspect", "alpine@sha256:5291449c3df73caf6ed85e649dec1b9e818b39a5d8c871e97afc13e9cd5e8fa8", "--format", "{{.Id}} {{json .RepoDigests}}"]),
        "image_build": run(["docker", "build", "--pull=false", "--network=none", "-t", IMAGE, str(ROOT)]),
        "cases": [],
    }
    base_inventory = inventory(ROOT / "base")
    plans = [
        {"id": "clean_single", "ops": ["printf 'single-v2\\n' > /workspace/single.txt"], "expected": {"C /workspace/single.txt"}, "files": {"single.txt": "single-v2\n"}, "accept": True},
        {"id": "clean_multi_rename", "ops": ["printf 'alpha-v2\\n' > /workspace/alpha.txt", "mv /workspace/beta.txt /workspace/gamma.txt", "printf 'new-v1\\n' > /workspace/new.txt"], "expected": {"C /workspace/alpha.txt", "D /workspace/beta.txt", "A /workspace/gamma.txt", "A /workspace/new.txt"}, "files": {"alpha.txt": "alpha-v2\n", "gamma.txt": "beta-v1\n", "new.txt": "new-v1\n"}, "accept": True},
        {"id": "clean_metadata_change", "ops": ["chmod 600 /workspace/single.txt"], "expected": {"C /workspace/single.txt"}, "files": {"single.txt": "base-single-v1\n"}, "accept": True, "mode": "600"},
        {"id": "partial_multifile_save", "ops": ["printf 'alpha-partial\\n' > /workspace/alpha.txt; exit 23"], "expected": {"C /workspace/alpha.txt"}, "files": {"alpha.txt": "alpha-partial\n", "beta.txt": "beta-v1\n"}, "accept": False, "injected_exit": 23},
        {"id": "network_effect_attempt", "ops": ["wget -T 1 -O /tmp/cow-out https://198.51.100.1/"], "expected": set(), "files": {"single.txt": "base-single-v1\n"}, "accept": False, "network_denied": True},
    ]
    # These states cannot be represented by the image filesystem. The frozen
    # admission rule refuses them before a container is created.
    refusals = ["dirty_open_buffer", "concurrent_base_revision_changed"]
    for plan in plans:
        cid = f"{PREFIX}-{plan['id']}"
        if run(["docker", "ps", "-aq", "--filter", f"name=^{cid}$"]).get("output", "").strip():
            raise SystemExit(f"STOP_CONTAINER_NAME_OCCUPIED:{cid}")
        create = run(["docker", "create", "--network", "none", "--ipc", "private", "--pids-limit", "32", "--name", cid, IMAGE, "sh", "-c", "sleep 30"])
        actual_id = create["output"].strip()
        run(["docker", "start", cid])
        results = []
        for op in plan["ops"]:
            results.append(run(["docker", "exec", cid, "sh", "-c", op], check=False))
            if results[-1]["exit"] and plan.get("injected_exit"):
                break
        run(["docker", "stop", cid])
        diff = run(["docker", "diff", cid])
        export = OUT / plan["id"]
        export.mkdir()
        cp = run(["docker", "cp", f"{cid}:/workspace/.", str(export)], check=False)
        inspect = run(["docker", "inspect", cid, "--format", "{{json .HostConfig}} {{json .State}}"])
        parsed_changes = set(line.strip() for line in diff["output"].splitlines() if line.strip())
        got_files = inventory(export)
        export_modes = {str(p.relative_to(export)): format(p.stat().st_mode & 0o777, "03o")
                        for p in sorted(export.rglob("*")) if p.is_file()}
        expected_files = {name: hashlib.sha256(data.encode()).hexdigest() for name, data in plan["files"].items()}
        record["cases"].append({
            "id": plan["id"], "container_id": actual_id, "base_inventory": base_inventory,
            "ops": results, "diff": diff, "diff_entries": sorted(parsed_changes),
            "export_cp": cp, "export_inventory": got_files, "expected_inventory": expected_files,
            "export_modes": export_modes,
            "inspect": inspect, "accept_expected": plan["accept"],
            "network_denied_expected": plan.get("network_denied", False),
            "mode_expected": plan.get("mode"),
            "decision": "ACCEPT_DELTA" if plan["accept"] else "REFUSE_INCOMPLETE_OR_EFFECT",
        })
        run(["docker", "rm", cid])
    for case_id in refusals:
        record["cases"].append({"id": case_id, "container_created": False, "decision": "REFUSE_UNPROVABLE_STATE"})
    # Disposable controls: direct-live mutates only its throwaway base; the
    # draft control edits a private versioned copy and leaves its base intact.
    controls = OUT / "controls"
    for control in ("direct_live", "native_draft"):
        root = controls / control
        if root.exists():
            raise SystemExit("STOP_CONTROL_PATH_EXISTS")
        (root / "base").mkdir(parents=True)
        shutil.copy2(ROOT / "base" / "single.txt", root / "base" / "single.txt")
        target = root / "base" / "single.txt" if control == "direct_live" else root / "draft" / "single.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        if control == "native_draft":
            shutil.copy2(root / "base" / "single.txt", target)
        target.write_text("single-v2\n")
    record["controls"] = {
        name: {"base_inventory": inventory(controls / name / "base"),
              "draft_inventory": inventory(controls / name / "draft") if (controls / name / "draft").exists() else None}
        for name in ("direct_live", "native_draft")
    }
    (OUT / "candidate.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"cases": len(record["cases"]), "output": str(OUT / "candidate.json")}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"CANDIDATE_STOP: {type(e).__name__}: {e}", file=sys.stderr)
        raise
