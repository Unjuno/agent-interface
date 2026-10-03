"""Read-only post-run custody verification; never launches a formal process."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
PREFIX = "research/analysis/" + ROOT.name + "/"
IMAGE_ID = "sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016"
GUEST = "/home/taka/outputs/phase-6969-a05-3cbf-02/"


def load_module(name):
    spec = importlib.util.spec_from_file_location("verify_" + name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require(ok, detail):
    if not ok:
        raise ValueError(detail)


def validate_runtime(role, inspection, receipt, observed):
    state, host, config = inspection["State"], inspection["HostConfig"], inspection["Config"]
    require(state["Status"] == "exited" and state["ExitCode"] == 0 and not state["OOMKilled"], "container not cleanly exited")
    require(inspection["RestartCount"] == 0 and not state["Running"], "container restarted or running")
    require(receipt["exit_code"] == 0 and not receipt["docker_stderr"], "launcher failure")
    require(inspection["Image"] == IMAGE_ID and config["User"] == "501:501", "image/user mismatch")
    require(host["NetworkMode"] == "none" and host["ReadonlyRootfs"] is True, "network/root isolation mismatch")
    require(host["Memory"] == 536870912 and host["NanoCpus"] == 1000000000, "configured resource mismatch")
    require(host["CapDrop"] == ["ALL"] and "no-new-privileges" in host["SecurityOpt"], "privilege isolation mismatch")
    require(observed == {"memory.max": "536870912", "cpu.max": "100000 100000"}, "observed resource mismatch")
    actual = sorted((m["Source"], m["Destination"], m["RW"]) for m in inspection["Mounts"] if m["Type"] == "bind")
    expected = [("/home/taka/inputs/phase-6969-a05-3cbf-02-" + role, "/src", False), (GUEST + role, "/out", True)]
    if role == "auditor":
        expected += [(GUEST + "candidate", "/candidate", False), (GUEST + "legacy", "/legacy", False)]
    require(actual == sorted(expected), "bind mount custody mismatch")


def verify(check_manifest=True):
    frozen = json.loads((ROOT / "FREEZE_02.json").read_text())
    for name, digest in frozen["source_sha256"].items():
        require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, "current freeze mismatch: " + name)
    git = "/Library/Developer/CommandLineTools/usr/bin/git" if Path("/Library/Developer/CommandLineTools/usr/bin/git").is_file() else shutil.which("git")
    old = json.loads((ROOT / "FREEZE.json").read_text())
    for name, digest in old["source_sha256"].items():
        content = subprocess.run([git, "show", frozen["predecessor_freeze_commit"] + ":" + PREFIX + name],
                                 cwd=ROOT, capture_output=True, check=True).stdout
        require(hashlib.sha256(content).hexdigest() == digest, "historical freeze mismatch: " + name)
    for name, digest in frozen["legacy_sha256"].items():
        path = ROOT.parent / "exogenous_opportunity_5694_matched_phase_a04_20261002" / name
        require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, "legacy source changed")
    require(all(frozen["source_sha256"][p] == old["source_sha256"][p]
                for p in ("candidate.py", "fixture.json", "audit.py", "legacy_probe.py", "prepare.py", "test_contract.py")),
            "scientific sources changed between allocations")
    consumed = json.loads((ROOT / "formal_02/CONSUMED.json").read_text())
    require(consumed["source_commit"] == "4b3da15ca4dbb4720e173475174c3a6c77169176", "source commit mismatch")
    runner = load_module("runner")
    runtime = {}
    for role in ("candidate", "legacy", "auditor"):
        inspection = json.loads((ROOT / "formal_02" / (role + ".inspect.json")).read_text())[0]
        receipt = json.loads((ROOT / "formal_02" / (role + ".receipt.json")).read_text())
        limits = {k: (ROOT / "formal_02" / role / k).read_text().strip() for k in ("memory.max", "cpu.max")}
        validate_runtime(role, inspection, receipt, limits)
        wanted_command = [runner.ORB, "run", "-m", runner.VM, "-u", "root", *runner.command(role)]
        require(receipt["command"] == wanted_command, "frozen invocation mismatch")
        require(inspection["Config"]["Cmd"] == runner.command(role)[-3:], "container entry command mismatch")
        require((ROOT / "formal_02" / role / "stderr.log").read_bytes() == b"", "nonempty process stderr")
        runtime[role] = {"container_id": inspection["Id"], "exit_code": inspection["State"]["ExitCode"],
                         "oom_killed": inspection["State"]["OOMKilled"], "observed_cgroup": limits,
                         "started_at_utc": inspection["State"]["StartedAt"],
                         "finished_at_utc": inspection["State"]["FinishedAt"]}
    fixture = json.loads((ROOT / "fixture.json").read_text())
    raw = json.loads((ROOT / "formal_02/candidate/raw.json").read_text())
    legacy = json.loads((ROOT / "formal_02/legacy/probe.json").read_text())
    retained = json.loads((ROOT / "formal_02/auditor/audit.json").read_text())
    audit = load_module("audit")
    require(not audit.errors(fixture, raw) and not audit.legacy_errors(legacy), "independent reconstruction mismatch")
    computed, copies = audit.audit(fixture, raw, legacy)
    require(audit.canonical(computed) == audit.canonical(retained), "retained audit mismatch")
    saved_copies = json.loads((ROOT / "formal_02/auditor/mutations.json").read_text())
    require(audit.canonical(copies) == audit.canonical(saved_copies), "retained mutation mismatch")
    require(retained["status"] == "PASS_METHOD_SCOPED" and not retained["errors"], "formal audit not passing")
    require(retained["boundary_counts"] == {"NOT_APPLICABLE": 1, "UNKNOWN": 3, "acquired_not_delivered": 2,
             "decision_no_effect": 2, "delivered_no_decision": 41, "eligible_effect_in_model": 76, "not_acquired": 22},
            "hand-derived finite counts mismatch")
    manifest_targets = 0
    if check_manifest:
        manifest = json.loads((ROOT / "MANIFEST_SHA256.json").read_text())
        present = sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*")
                         if p.is_file() and "__pycache__" not in p.parts and p.name != "MANIFEST_SHA256.json")
        require(present == sorted(manifest), "manifest does not cover every retained package file")
        for name, digest in manifest.items():
            require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, "artifact SHA256 mismatch: " + name)
        manifest_targets = len(manifest)
    return {"status": "PASS_METHOD_SCOPED; HOLD_LIVE_TRANSFER", "issue": 6969, "predecessor": 6803,
            "intake_main": frozen["intake_main"], "source_freeze_commit": consumed["source_commit"],
            "allocation": frozen["allocation"], "formal_invocations": {r: 1 for r in runtime}, "retries": 0,
            "runtime": runtime, "metrics": {k: retained[k] for k in ("rows_checked", "grid_cells", "controls", "boundary_counts", "matched_contrasts", "legacy_probe_inputs", "legacy_onset_only_pairs_insensitive")},
            "mutation_controls_rejected": sum(c["rejected"] for c in retained["mutation_controls"]),
            "authority_events": 0, "live_effect_events": 0, "manifest_targets_verified": manifest_targets}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-run", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    if args.write_run:
        summary = verify(check_manifest=False)
        summary.pop("manifest_targets_verified")
        with (ROOT / "RUN.json").open("x") as target:
            json.dump(summary, target, sort_keys=True, indent=2)
            target.write("\n")
    elif args.write_manifest:
        files = sorted(p for p in ROOT.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.name != "MANIFEST_SHA256.json")
        with (ROOT / "MANIFEST_SHA256.json").open("x") as target:
            json.dump({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}, target, sort_keys=True, indent=2)
            target.write("\n")
    else:
        print(json.dumps(verify(), sort_keys=True, indent=2))
