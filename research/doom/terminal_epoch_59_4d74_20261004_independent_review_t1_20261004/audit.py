"""Independent saved-data and source-binding review for terminal epoch 01."""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "research/doom/terminal_epoch_59_4d74_20261004"
HERE = Path(__file__).resolve().parent


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_bytes(revision: str, path: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{revision}:{path}"], cwd=REPO)


def verify_package_manifest() -> int:
    manifest = SOURCE / "FILES.sha256"
    expected: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        assert len(digest) == 64
        assert relative not in expected
        expected[relative] = digest
    actual = {path.relative_to(SOURCE).as_posix()
              for path in SOURCE.rglob("*") if path.is_file()} - {"FILES.sha256"}
    assert actual == set(expected), {
        "unlisted": sorted(actual - set(expected)),
        "missing": sorted(set(expected) - actual),
    }
    for relative, digest in expected.items():
        assert sha((SOURCE / relative).read_bytes()) == digest, relative
    return len(expected)


def main() -> None:
    freeze = json.loads((SOURCE / "out/FREEZE.json").read_text(encoding="utf-8"))
    result = json.loads((SOURCE / "out/RESULT.json").read_text(encoding="utf-8"))
    exit_receipt = json.loads((SOURCE / "out/exit.json").read_text(encoding="utf-8"))
    stdout = json.loads((SOURCE / "out/stdout.txt").read_text(encoding="utf-8"))
    stderr = (SOURCE / "out/stderr.txt").read_text(encoding="utf-8")

    manifest_count = verify_package_manifest()
    source_commit = freeze["source_commit"]
    review_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    subprocess.run(["git", "merge-base", "--is-ancestor", source_commit, "HEAD"],
                   cwd=REPO, check=True, capture_output=True)

    source_paths = {
        "independent_progress_clock_v2.py":
            "research/doom/independent_progress_clock_v2.py",
        "session_map01_v15.py": "research/doom/session_map01_v15.py",
    }
    for name, path in source_paths.items():
        pinned = git_bytes(source_commit, path)
        retained = (SOURCE / "source" / name).read_bytes()
        assert sha(pinned) == sha(retained) == freeze["members"][name], name

    probe_path = SOURCE / "source/probe.py"
    assert sha(probe_path.read_bytes()) == freeze["members"]["probe.py"]
    probe_tree = ast.parse(probe_path.read_bytes())
    called = {node.func.attr for node in ast.walk(probe_tree)
              if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    assert "set_available_buttons" in called
    assert "advance_action" in called
    assert not called.intersection({"make_action", "set_action", "send_game_command"})
    calls = [node for node in ast.walk(probe_tree)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
    assert any(node.func.attr == "set_available_buttons" and len(node.args) == 1 and
               isinstance(node.args[0], ast.List) and not node.args[0].elts
               for node in calls)
    assert any(node.func.attr == "advance_action" and len(node.args) == 2 and
               isinstance(node.args[0], ast.Constant) and node.args[0].value == 1 and
               isinstance(node.args[1], ast.Constant) and node.args[1].value is True
               for node in calls)
    assert any(node.func.attr == "set_episode_timeout" and node.args and
               isinstance(node.args[0], ast.Constant) and node.args[0].value == 70
               for node in calls)
    assert any(node.func.attr == "ingest" and node.args and
               isinstance(node.args[0], ast.Call) and
               isinstance(node.args[0].func, ast.Name) and
               node.args[0].func.id == "replace" and
               any(keyword.arg == "sample_ns" and
                   isinstance(keyword.value, ast.Call) and
                   isinstance(keyword.value.func, ast.Attribute) and
                   keyword.value.func.attr == "perf_counter_ns"
                   for keyword in node.args[0].keywords)
               for node in calls)
    assert "vizdoom" in {alias.name for node in probe_tree.body
                          if isinstance(node, ast.Import) for alias in node.names}

    argv = freeze["argv"]
    assert argv[0].lower().endswith("wslc.exe")
    assert "--network" in argv and argv[argv.index("--network") + 1] == "none"
    assert "--pull" in argv and argv[argv.index("--pull") + 1] == "never"
    assert "--user" in argv and argv[argv.index("--user") + 1] == "65534:65534"
    assert "--cpus" in argv and argv[argv.index("--cpus") + 1] == "1"
    assert "--memory" in argv and argv[argv.index("--memory") + 1] == "512m"
    mounts = [argv[i + 1] for i, value in enumerate(argv[:-1]) if value == "-v"]
    assert len(mounts) == 3
    assert any(mount.endswith(":/source:ro") for mount in mounts)
    assert any(mount.endswith(":/wad:ro") for mount in mounts)
    assert any(mount.endswith(":/out:rw") for mount in mounts)

    rows = result["rows"]
    assert len(rows) == 57
    assert [row["index"] for row in rows] == list(range(57))
    tics = [row["producer_tic_before"] for row in rows]
    assert (tics[0], tics[-1]) == (5, 71)
    assert all(left < right for left, right in zip(tics, tics[1:]))
    assert all(row["producer_tic_before"] == row["producer_tic_after"] for row in rows)
    assert all(row["ack_requested_ns"] <= row["ack_returned_ns"] <=
               row["sample"]["sample_ns"] for row in rows)
    sample_times = [row["sample"]["sample_ns"] for row in rows]
    assert all(left < right for left, right in zip(sample_times, sample_times[1:]))
    assert all(row["frame_tic"] == row["producer_tic_after"] for row in rows[:-1])
    assert rows[-1]["frame_tic"] is None
    assert all(row["sample"]["episode_finished"] is False for row in rows[:-1])
    terminal = rows[-1]["sample"]
    assert terminal["episode_finished"] is True
    assert terminal["player_dead"] is False and terminal["map_exit"] is False

    flattened = [event for row in rows for event in row["events"]]
    assert flattened == result["events"] and len(flattened) == 1
    event = flattened[0]
    assert event == rows[-1]["events"][0]
    assert event["event_sequence"] == 1
    assert event["kind"] == "EPISODE_FINISHED_NO_EXIT"
    assert event["polarity"] == "negative"
    assert event["useful"] is False and event["controller_visible"] is False
    assert event["observed_ns"] == terminal["sample_ns"]
    assert event["before"] == {"episode_finished": False}
    assert event["after"] == {
        "episode_finished": True, "player_dead": False, "map_exit": False}
    assert result["repeat_terminal_events"] == []
    assert result["positive_input_calls"] == 0
    assert result["close_returned"] is True
    assert result["running_after_close"] is False
    assert result["status"] == "PASS_ACKNOWLEDGED_TERMINAL_PIPELINE_SCOPED"
    assert exit_receipt["exit_code"] == 0
    assert stdout["status"] == result["status"] and stdout["rows"] == 57
    assert stdout["events"] == result["events"]
    assert "swap limit capabilities" in stderr and "cgroup" in stderr

    durations = [(row["ack_returned_ns"] - row["ack_requested_ns"]) / 1e6
                 for row in rows]
    audit = {
        "schema": "terminal-epoch-saved-data-review-v1",
        "disposition": "PASS_TRACE_AND_SOURCE_BINDING_WITH_SCOPE_LIMITATIONS",
        "review_head": review_head,
        "source_commit": source_commit,
        "source_commit_ancestor_of_review_head": True,
        "manifest_files_verified": manifest_count,
        "source_files_bound_to_frozen_commit": sorted(source_paths),
        "probe_source_sha256": sha(probe_path.read_bytes()),
        "probe_source_contract": {
            "empty_available_button_set": True,
            "only_advance_action_one_tic_update_true": True,
            "episode_timeout_tics": 70,
            "repeat_terminal_uses_later_monotonic_timestamp": True,
            "game_action_emission_calls": 0,
        },
        "trace": {
            "rows": len(rows), "producer_tic_start_end": [tics[0], tics[-1]],
            "strictly_advancing_producer_tics": True,
            "per_ack_tics_equal": True,
            "frame_tic_matches": 56, "events": len(flattened),
            "terminal_event": event["kind"],
            "terminal_event_negative_unuseful_invisible": True,
            "duplicate_terminal_events": len(result["repeat_terminal_events"]),
            "positive_input_calls": result["positive_input_calls"],
            "close_returned": result["close_returned"],
            "running_after_close": result["running_after_close"],
            "ack_duration_ms_min_max": [min(durations), max(durations)],
        },
        "limitations": [
            "The WAD bytes are absent; only their declared SHA-256 is retained.",
            "The host cgroup/swap warning means the requested memory cap is not independently established.",
            "The retained repeated-terminal receipt stores no repeated sample timestamp; the probe source shows that it reuses the exact state with a later perf_counter_ns value, while the result stores only the empty event list.",
            "The trace does not independently establish engine timeout onset, neutral cadence, positive task effect, physical input release, or gameplay efficacy.",
            "This is a saved-data audit; no runtime, container, game, model, GUI, or input was started.",
        ],
    }
    (HERE / "audit-result.json").write_text(json.dumps(audit, indent=2) + "\n",
                                            encoding="utf-8")
    print("PASS: 11 source-package files, frozen source ancestry, and 57-row trace verified")
    print(f"ack_duration_ms_min_max={min(durations):.6f},{max(durations):.6f}")
    print("scope=trace/source binding only; execution environment and task efficacy unverified")


if __name__ == "__main__":
    main()
