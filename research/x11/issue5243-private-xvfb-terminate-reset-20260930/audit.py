#!/usr/bin/env python3
"""Strict raw auditor and five single-field corruption controls."""
import copy
import json
import sys
from pathlib import Path


def require(ok, message):
    if not ok:
        raise ValueError(message)


def audit(r):
    c = r["child"]
    require(r["schema"] == "issue5243-xvfb-reset-host-v1", "host schema")
    require(r["timeout"] is False and r["exit_code"] == 0, "wrapper exit/timeout")
    require(r["host_socket_unchanged"] is True and r["host_socket_before"] == r["host_socket_after"], "host socket metadata")
    require(c["schema"] == "issue5243-xvfb-reset-child-v1", "child schema")
    require(c["host_mount_ns_inode"] == r["host_mount_ns_inode"], "cross-record host namespace identity")
    require(c["namespace_private"] is True and c["child_mount_ns_inode"] != c["host_mount_ns_inode"], "namespace identity")
    m = c["socket_mount"]
    require(m["target"] == "/tmp/.X11-unix" and m["fstype"] == "tmpfs", "private tmpfs mount")
    require(m["source"] in ("none", "tmpfs"), "tmpfs mount source token")
    require(c["socket_dir_mode"] == 0o1777, "socket directory mode")
    require(c["noreset_used"] is False and "-terminate" in c["xvfb_args"], "termination options")
    require(c["xvfb_ready"] is True and c["display"] == ":98" and c["screen"] == [640, 480], "Xlib readiness")
    require(c["x_socket_exists"] is True, "private socket")
    require(c["natural_exit"] is True and c["xvfb_exit_code"] == 0, "natural server exit")
    return {"status": "PASS_PRIVATE_XVFB_RESET_TERMINATION_CONSTRUCTION_ONLY", "checks": 12}


def mutation_controls(record):
    mutations = {
        "namespace_identity": lambda x: x["child"].update(namespace_private=False),
        "cross_record_host_namespace": lambda x: x["child"].update(host_mount_ns_inode=x["host_mount_ns_inode"] + 1),
        "mount_target_or_type": lambda x: x["child"].update(socket_mount={"target": "/tmp", "fstype": "tmpfs", "source": "none"}),
        "xlib_readiness": lambda x: x["child"].update(xvfb_ready=False),
        "natural_process_exit": lambda x: x["child"].update(natural_exit=False),
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
    require(len(rejected) == len(mutations), "mutation control accepted")
    return rejected


if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text())
    result = audit(data)
    result["corruption_controls_rejected"] = mutation_controls(data)
    print(json.dumps(result, sort_keys=True))
