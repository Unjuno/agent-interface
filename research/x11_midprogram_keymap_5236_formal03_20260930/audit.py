"""Independent raw-only decision auditor for Issue #5236 formal02."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EXPECTED_ROWS = (
    ("control_us", "us", None),
    ("jp_to_us", "jp", "us"),
    ("us_to_jp", "us", "jp"),
)
EXPECTED_EFFECT_HEX = "7b227361766564223a20747275652c202274657874223a2022615f227d0a"


def _layout(stdout: str | None) -> str | None:
    if not isinstance(stdout, str):
        return None
    match = re.search(r"(?m)^layout:\s*(\S+)\s*$", stdout)
    return match.group(1) if match else None


def _verified_release(row: dict) -> bool:
    execution = row.get("dispatch", {}).get("execution", {})
    releases = execution.get("releases")
    return (isinstance(releases, list) and bool(releases) and all(
        isinstance(release, dict)
        and release.get("verified") is True
        and release.get("keys_down") == []
        and release.get("buttons_down") == []
        for release in releases
    ))


def audit(raw: dict, wrapper: dict | None = None) -> dict:
    reasons: list[str] = []
    if raw.get("schema") != "issue5236-formal03-raw-v1":
        return {"decision": "STOP_PROVENANCE_OR_RUNNER", "reasons": ["raw schema"]}
    if (not isinstance(wrapper, dict)
            or wrapper.get("schema") != "issue5236-formal03-wrapper-v1"
            or wrapper.get("timeout") is not False
            or wrapper.get("returncode") != 0
            or wrapper.get("child_raw_available") is not True):
        return {"decision": "STOP_PROVENANCE_OR_RUNNER", "reasons": ["wrapper status"]}
    command = wrapper.get("command")
    if (not isinstance(command, list)
            or command[:5] != ["unshare", "--user", "--map-root-user", "--mount", "--fork"]
            or "--child" not in command):
        reasons.append("namespace wrapper command")
    manifest = wrapper.get("source_manifest")
    if (raw.get("source_manifest") != manifest
            or not isinstance(manifest, dict)
            or raw.get("source_blobs") != manifest.get("files")):
        reasons.append("source manifest binding")
    before, after = wrapper.get("host_socket_before"), wrapper.get("host_socket_after")
    if (wrapper.get("host_socket_unchanged") is not True or not isinstance(before, dict)
            or before != after):
        reasons.append("host socket metadata changed/missing")
    namespace = raw.get("namespace")
    if not isinstance(namespace, dict):
        reasons.append("missing namespace record")
    else:
        if (namespace.get("host_mount_ns_inode") != wrapper.get("host_mount_ns_inode")
                or namespace.get("child_mount_ns_inode") == wrapper.get("host_mount_ns_inode")
                or namespace.get("private") is not True):
            reasons.append("namespace identity binding")
        mount = namespace.get("socket_mount")
        if (not isinstance(mount, dict) or mount.get("target") != "/tmp/.X11-unix"
                or mount.get("fstype") != "tmpfs" or mount.get("source") not in {"none", "tmpfs"}
                or namespace.get("socket_dir_mode") != 0o1777):
            reasons.append("private socket tmpfs/mode")
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED_ROWS):
        return {"decision": "STOP_PROVENANCE_OR_RUNNER", "reasons": ["row count"]}

    row_kinds: dict[str, str] = {}
    stale_effect = False
    for row, (row_id, initial, target) in zip(rows, EXPECTED_ROWS, strict=True):
        if not isinstance(row, dict) or row.get("row") != row_id:
            reasons.append(f"row order/id: {row_id}")
            continue
        if row.get("initial_layout") != initial or row.get("target_layout") != target:
            reasons.append(f"layout plan: {row_id}")
        final_layout = target or initial
        setup = row.get("layout_setup", {})
        initial_readback = row.get("layout_initial", {})
        final_readback = row.get("layout_after", {})
        if setup.get("exit") != 0:
            reasons.append(f"layout setup exit: {row_id}")
        if (initial_readback.get("exit") != 0
                or _layout(initial_readback.get("stdout")) != initial):
            reasons.append(f"initial layout readback: {row_id}")
        if (final_readback.get("exit") != 0
                or _layout(final_readback.get("stdout")) != final_layout):
            reasons.append(f"final layout readback: {row_id}")
        display_name = row.get("display")
        if setup.get("argv") != ["setxkbmap", "-display", display_name, "-layout", initial]:
            reasons.append(f"layout setup argv: {row_id}")
        for readback in (initial_readback, final_readback):
            if readback.get("argv") != ["setxkbmap", "-display", display_name, "-query"]:
                reasons.append(f"layout query argv: {row_id}")
        expected_program_ops = [
            {"op": "focus", "target": "fixture"},
            {"op": "text", "text": "a"},
            {"op": "wait_update", "timeout_ms": 1500},
            {"op": "text", "text": "_"},
            {"op": "key_chord", "keys": ["CTRL", "S"]},
            {"op": "release_all"},
        ]
        program = row.get("program", {})
        if (program.get("schema") != "agent-interface/program-v1"
                or program.get("program_id") != "issue5236-formal03-" + row_id
                or program.get("ops") != expected_program_ops
                or program.get("source") != {"observation_seq": 7, "binding_revision": 3}
                or program.get("terminal") != {"release_all_required": True}):
            reasons.append(f"program bytes/shape: {row_id}")
        if row.get("fixture_exit") != -15:
            reasons.append(f"fixture cleanup: {row_id}")
        xvfb_args = row.get("xvfb", {}).get("argv", [])
        expected_xvfb = ["Xvfb", "-displayfd", "1", "-screen", "0", "1024x768x24",
                         "-nolisten", "tcp", "-terminate", "-ac"]
        if xvfb_args != expected_xvfb:
            reasons.append(f"Xvfb argv: {row_id}")
        if row.get("expected_effect_hex") != EXPECTED_EFFECT_HEX:
            reasons.append(f"expected effect bytes: {row_id}")
        if row.get("xvfb", {}).get("exit_code") != 0 or row.get("xvfb", {}).get("cleanup_action") != "natural_terminate":
            reasons.append(f"Xvfb cleanup: {row_id}")
        if not _verified_release(row):
            reasons.append(f"neutral release: {row_id}")

        dispatch = row.get("dispatch")
        execution = dispatch.get("execution", {}) if isinstance(dispatch, dict) else {}
        status = dispatch.get("status") if isinstance(dispatch, dict) else None
        waits = execution.get("waits")
        wait = row.get("wait")
        if (not isinstance(wait, dict) or not isinstance(waits, list) or len(waits) != 1
                or waits[0] != wait or wait.get("started_ns", 0) >= wait.get("ended_ns", 0)):
            reasons.append(f"wait receipt: {row_id}")
        actor = row.get("actor_receipt")
        if target is None:
            if actor is not None or row.get("actor_argv") is not None or row.get("actor_exit") is not None:
                reasons.append(f"unexpected actor: {row_id}")
        else:
            if not isinstance(actor, dict):
                reasons.append(f"missing actor receipt: {row_id}")
            else:
                expected_actor_argv = ["setxkbmap", "-display", display_name, "-layout", target]
                recorded_actor_argv = row.get("actor_argv")
                if (not isinstance(recorded_actor_argv, list)
                        or len(recorded_actor_argv) < 6
                        or recorded_actor_argv[1] != "-c"
                        or recorded_actor_argv[-3:-1] != [display_name, target]
                        or actor.get("argv") != expected_actor_argv):
                    reasons.append(f"actor argv: {row_id}")
                if (actor.get("target_layout") != target or actor.get("exit") != 0
                        or not isinstance(wait, dict)
                        or not (wait.get("started_ns", 0) <= actor.get("started_ns", -1)
                                <= actor.get("ended_ns", -1) <= wait.get("ended_ns", 0))):
                    reasons.append(f"actor timing/receipt: {row_id}")

        effect = row.get("saved_effect_hex")
        if target is None:
            if status != "completed" or effect != EXPECTED_EFFECT_HEX:
                reasons.append("control row effect/status")
            else:
                row_kinds[row_id] = "exact"
        elif status == "completed":
            if effect != EXPECTED_EFFECT_HEX:
                if effect is not None:
                    stale_effect = True
                else:
                    reasons.append(f"missing completed effect: {row_id}")
            else:
                row_kinds[row_id] = "exact"
            if execution.get("completed_ops") != [0, 1, 2, 3, 4, 5]:
                reasons.append(f"completed operation receipt: {row_id}")
        elif status == "execution_failed":
            if (execution.get("failed_op") != 3 or execution.get("completed_ops") != [0, 1, 2]
                    or effect is not None):
                reasons.append(f"failure boundary/effect: {row_id}")
            else:
                row_kinds[row_id] = "refused"
        else:
            reasons.append(f"dispatch status: {row_id}")

    if stale_effect:
        decision = "FAIL_STALE_MAP_EFFECT"
    elif reasons:
        decision = "STOP_PROVENANCE_OR_RUNNER"
    elif all(row_kinds.get(row) == "refused" for row in ("jp_to_us", "us_to_jp")):
        decision = "PASS_MIDPROGRAM_REMAP_FAIL_CLOSED"
    elif all(row_kinds.get(row) == "exact" for row in ("jp_to_us", "us_to_jp")):
        decision = "NO_STALE_EFFECT_OBSERVED"
    else:
        decision = "STOP_PROVENANCE_OR_RUNNER"
        reasons.append("mixed remap outcomes")
    return {"decision": decision, "reasons": reasons, "rows": row_kinds}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print("usage: audit.py RAW.json WRAPPER.json", file=sys.stderr)
        return 2
    try:
        raw = json.loads(Path(args[0]).read_text(encoding="utf-8"))
        wrapper = json.loads(Path(args[1]).read_text(encoding="utf-8"))
        result = audit(raw, wrapper)
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        print(f"STOP_AUDIT_INPUT: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
