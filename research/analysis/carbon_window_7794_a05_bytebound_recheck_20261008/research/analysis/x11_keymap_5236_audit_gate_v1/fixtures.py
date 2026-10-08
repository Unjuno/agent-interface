"""Independent, synthetic, in-memory evidence builders; no runner imports."""
from copy import deepcopy


EXPECTED_EFFECT = b'{"saved": true, "text": "a_"}\n'.hex()
WRONG_EFFECT = b'{"saved": true, "text": "a="}\n'.hex()


def evidence():
    """Build a fresh completed three-row record and matching synthetic wrapper."""
    manifest = {"files": {"synthetic-fixture.py": "1" * 40}}
    wrapper = {
        "schema": "issue5236-formal06-wrapper-v1",
        "timeout": False,
        "returncode": 0,
        "child_raw_available": True,
        "fixture_preflight": {"returncode": 0, "stdout": "fixture_import tkinter"},
        "repository_root": "/synthetic",
        "runner_path": "/synthetic/never-executed.py",
        "python_executable": "/synthetic/python",
        "command": [
            "unshare", "--user", "--map-root-user", "--mount", "--fork",
            "/synthetic/python", "-c",
            "sys.path.insert(0,'/synthetic'); "
            "runpy.run_path('/synthetic/never-executed.py'); "
            "'--child' '--child-output' '--host-namespace'",
        ],
        "source_manifest": deepcopy(manifest),
        "host_mount_ns_inode": 10,
        "host_socket_before": {"inode": 20, "device": 30, "mode": 0o777},
        "host_socket_after": {"inode": 20, "device": 30, "mode": 0o777},
        "host_socket_unchanged": True,
    }
    rows = []
    for row_id, initial, target in (
        ("control_us", "us", None),
        ("jp_to_us", "jp", "us"),
        ("us_to_jp", "us", "jp"),
    ):
        display = ":synthetic"
        wait = {"started_ns": 1000, "ended_ns": 2000}
        post_save_wait = {
            "started_ns": 2100, "ended_ns": 2400,
            "requested_ms": 250, "operation_index": 8,
        }
        row = {
            "row": row_id,
            "display": display,
            "initial_layout": initial,
            "target_layout": target,
            "layout_setup": {
                "argv": ["setxkbmap", "-display", display, "-layout", initial],
                "exit": 0,
            },
            "layout_initial": {
                "argv": ["setxkbmap", "-display", display, "-query"],
                "exit": 0, "stdout": "layout: " + initial + "\n",
            },
            "layout_after": {
                "argv": ["setxkbmap", "-display", display, "-query"],
                "exit": 0, "stdout": "layout: " + (target or initial) + "\n",
            },
            "program": {
                "schema": "agent-interface/program-v1",
                "program_id": "issue5236-formal06-" + row_id,
                "source": {"observation_seq": 7, "binding_revision": 3},
                "terminal": {"release_all_required": True},
                "ops": [
                    {"op": "focus", "target": "fixture"},
                    {"op": "pointer_move", "target": "fixture", "frame": "window_client", "x": 50, "y": 55},
                    {"op": "pointer_button", "button": "left", "down": True},
                    {"op": "pointer_button", "button": "left", "down": False},
                    {"op": "text", "text": "a"},
                    {"op": "wait_update", "timeout_ms": 1500},
                    {"op": "text", "text": "_"},
                    {"op": "key_chord", "keys": ["CTRL", "S"]},
                    {"op": "wait_update", "timeout_ms": 250},
                    {"op": "release_all"},
                ],
            },
            "fixture_exit": -15,
            "xvfb": {
                "argv": ["Xvfb", "-displayfd", "1", "-screen", "0", "1024x768x24", "-nolisten", "tcp", "-terminate", "-ac"],
                "exit_code": 0, "cleanup_action": "natural_terminate",
            },
            "expected_effect_hex": EXPECTED_EFFECT,
            "saved_effect_hex": EXPECTED_EFFECT,
            "wait": deepcopy(wait),
            "post_save_wait": deepcopy(post_save_wait),
            "dispatch": {
                "status": "completed",
                "execution": {
                    "completed_ops": list(range(10)),
                    "waits": [deepcopy(wait), deepcopy(post_save_wait)],
                    "releases": [{"verified": True, "keys_down": [], "buttons_down": []}],
                },
            },
            "actor_receipt": None,
            "actor_argv": None,
            "actor_exit": None,
        }
        if target is not None:
            row["actor_receipt"] = {
                "argv": ["setxkbmap", "-display", display, "-layout", target],
                "target_layout": target, "exit": 0,
                "started_ns": 1200, "ended_ns": 1300,
            }
            row["actor_argv"] = ["synthetic-python", "-c", "never executed", display, target, "synthetic.json"]
            row["actor_exit"] = 0
        rows.append(row)
    raw = {
        "schema": "issue5236-formal06-raw-v1",
        "source_manifest": deepcopy(manifest),
        "source_blobs": deepcopy(manifest["files"]),
        "namespace": {
            "host_mount_ns_inode": 10, "child_mount_ns_inode": 11, "private": True,
            "socket_mount": {"target": "/tmp/.X11-unix", "fstype": "tmpfs", "source": "none"},
            "socket_dir_mode": 0o1777,
        },
        "rows": rows,
    }
    return raw, wrapper


def refuse(row):
    """Make one synthetic remap a correctly evidenced op-6 refusal."""
    row["saved_effect_hex"] = None
    row["post_save_wait"] = None
    row["dispatch"] = {
        "status": "execution_failed",
        "execution": {
            "failed_op": 6,
            "completed_ops": list(range(6)),
            "waits": [deepcopy(row["wait"])],
            "releases": [{"verified": True, "keys_down": [], "buttons_down": []}],
        },
    }


PROVENANCE_CASES = (
    ("omitted_row", "row count"),
    ("swapped_direction", "row order/id: jp_to_us"),
    ("wrong_expected_bytes", "expected effect bytes: jp_to_us"),
    ("missing_actor_receipt", "missing actor receipt: jp_to_us"),
    ("missing_post_save_wait", "wait receipt: jp_to_us"),
)


def mutate(raw, name):
    """Return a new record with one named, explicit structural mutation."""
    value = deepcopy(raw)
    if name == "omitted_row":
        value["rows"].pop()
    elif name == "swapped_direction":
        value["rows"][1:3] = value["rows"][2:0:-1]
    elif name == "wrong_expected_bytes":
        value["rows"][1]["expected_effect_hex"] = "00"
    elif name == "missing_actor_receipt":
        value["rows"][1]["actor_receipt"] = None
    elif name == "missing_post_save_wait":
        value["rows"][1]["post_save_wait"] = None
    else:
        raise ValueError("Unknown synthetic mutation: " + name)
    return value
