#!/usr/bin/env python3
"""Independent strict audit and five single-field corruption controls."""
import copy
import json
import sys
from pathlib import Path


def require(ok, message):
    if not ok:
        raise ValueError(message)


def audit(r):
    c = r["child"]
    require(r["schema"] == "issue5243-private-xvfb-host-wrapper-v1", "host schema")
    require(r["timeout"] is False and r["exit_code"] == 0, "wrapper exit/timeout")
    require(r["host_socket_unchanged"] is True, "host socket changed")
    require(r["host_socket_before"] == r["host_socket_after"], "host socket metadata mismatch")
    require(c["schema"] == "issue5243-private-xvfb-construction-v1", "child schema")
    require(c["namespace_private"] is True, "namespace not private")
    require(c["child_mount_ns_inode"] != c["host_mount_ns_inode"], "namespace identity")
    require(c["socket_mount"] == {"target": "/tmp/.X11-unix", "fstype": "tmpfs", "source": "tmpfs"}, "private tmpfs mount")
    require(c["socket_dir_mode"] == 0o1777, "socket directory mode")
    require(c["xvfb_ready"] is True and c["display"] == ":97", "Xvfb readiness")
    require(c["screen"] == [640, 480], "screen geometry")
    require(c["x_socket_exists"] is True, "private X socket missing")
    require(c["xvfb_exit_code"] == 0, "Xvfb process exit")
    return {"status": "PASS_PRIVATE_XVFB_CONSTRUCTION_ONLY", "checks": 11}


def mutation_controls(record):
    mutations = {
        "namespace_identity": lambda x: x["child"].update(namespace_private=False),
        "mount_target_or_type": lambda x: x["child"].update(socket_mount={"target": "/tmp", "fstype": "tmpfs", "source": "tmpfs"}),
        "xvfb_readiness": lambda x: x["child"].update(xvfb_ready=False),
        "process_exit": lambda x: x["child"].update(xvfb_exit_code=7),
        "host_socket_identity": lambda x: x.update(host_socket_unchanged=False),
    }
    rejected = []
    for name, mutate in mutations.items():
        changed = copy.deepcopy(record)
        mutate(changed)
        try:
            audit(changed)
        except (KeyError, ValueError):
            rejected.append(name)
    require(len(rejected) == len(mutations), "one or more corruption controls accepted")
    return rejected


if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text())
    result = audit(data)
    result["corruption_controls_rejected"] = mutation_controls(data)
    print(json.dumps(result, sort_keys=True))
