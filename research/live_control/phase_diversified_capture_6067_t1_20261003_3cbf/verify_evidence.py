"""Saved-only custody gate, never a producer/admission or scientific success."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent

def need(condition, why):
    if not condition:
        raise ValueError(why)

def check_runtime(runtime, image):
    need(runtime["Image"] == image, "actual image identity")
    need(type(runtime["RestartCount"]) is int and runtime["RestartCount"] == 0, "no restart")
    state, host = runtime["State"], runtime["HostConfig"]
    need(state["Running"] is False and state["OOMKilled"] is False, "terminal, no OOM")
    code = state["ExitCode"]
    need(type(code) is int and code in (0, 2), "exact terminal 0/2")
    need(runtime["Config"]["User"] == "501:501", "non-root run user")
    expected = {"NanoCpus": 1_000_000_000, "Memory": 536870912,
                "MemorySwap": 536870912, "PidsLimit": 64, "NetworkMode": "none",
                "ReadonlyRootfs": True, "Privileged": False}
    for k, v in expected.items():
        need(type(host[k]) is type(v) and host[k] == v, "actual isolation: " + k)
    need(host["CapDrop"] == ["ALL"] and "no-new-privileges" in host["SecurityOpt"], "no authority expansion")
    need(not host["Devices"] and not host["DeviceRequests"], "no GPU/device requests")
    return code

def read(name):
    return json.loads((HERE / name).read_text())

def main():
    freeze = read("FREEZE.json")
    pins = dict(freeze["candidate_sha256"], **{"audit.py": freeze["auditor_sha256"]})
    git = os.environ.get("PHASE6067_GIT", "git")
    root = Path(subprocess.check_output([git, "rev-parse", "--show-toplevel"], cwd=HERE, text=True).strip())
    for name, expected in pins.items():
        relative = (HERE / name).relative_to(root).as_posix()
        original = subprocess.check_output([git, "show", freeze["source_commit"] + ":" + relative], cwd=HERE)
        need(hashlib.sha256(original).hexdigest() == expected, "published source pin: " + name)
        need(hashlib.sha256((HERE / name).read_bytes()).hexdigest() == expected, "current retained source: " + name)
    for name in ("guest-source-pre.json", "guest-source-post.json"):
        guest = read(name)
        need(guest == pins, "staged guest source custody: " + name)
    run = read("formal-container.json")
    code = check_runtime(run, freeze["image_id"])
    need(run["Config"]["Cmd"] == freeze["candidate_command"][freeze["candidate_command"].index("python3"):], "candidate command")
    mounts = {m["Destination"]: m for m in run["Mounts"]}
    need(mounts["/src"]["RW"] is False and mounts["/out"]["RW"] is True, "exact mount permissions")
    need(mounts["/src"]["Source"] == "/home/taka/inputs/phase-6067-x11-3cbf-source-48ce12", "exact frozen source root")
    need(mounts["/out"]["Source"] == "/home/taka/outputs/phase-6067-x11-3cbf-formal-a01", "exact fresh output root")
    raw, fixture = read("formal/raw.json"), read("fixture.json")
    need(raw["source_sha256"] == freeze["candidate_sha256"], "in-run source hashes")
    need(raw["mode"] == "formal" and raw["allocation"] == freeze["allocation"], "formal identity")
    planned = [c["id"] for c in fixture["cases"]]
    started, completed = raw["started_cells"], raw["cells"]
    need(started == planned[:len(started)] and completed == planned[:len(completed)], "no replay/substitution")
    need(raw["cgroups"] == {"cpu.max": "100000 100000", "memory.max": "536870912",
                           "memory.swap.max": "0", "pids.max": "64"}, "in-run cgroups")
    if code == 2:
        need(raw["status"] == "STOP" and len(started) == len(completed) + 1, "first failed cell retained")
        need(not (HERE / "audit").exists(), "no auditor after failed producer")
        science = "STOP_NO_COMPLETE_TRANSFER_CLAIM"
    else:
        need(raw["status"] == "COMPLETE" and completed == planned and started == planned, "complete finite block")
        auditor = read("auditor-container.json")
        need(check_runtime(auditor, freeze["image_id"]) == 0, "separate auditor terminal0")
        need(auditor["Config"]["Cmd"] == freeze["auditor_command"][freeze["auditor_command"].index("python3"):], "auditor command")
        need(run["State"]["FinishedAt"] < auditor["State"]["StartedAt"], "auditor admitted only after producer terminal")
        import audit
        actual = audit.validate(HERE / "formal", fixture, freeze["candidate_sha256"])
        need(actual == read("audit/audit.json"), "saved-only independent recount")
        mutations = read("audit/mutations.json")
        need(len(mutations) == 8 and all(m["rejected"] is True for m in mutations), "eight corruptions refused")
        science = actual["status"]
    print(json.dumps({"custody": "VERIFIED_SAVED_ONLY", "scientific_status": science,
                      "completed_cells": len(completed), "started_cells": len(started)}, sort_keys=True))

if __name__ == "__main__":
    main()
