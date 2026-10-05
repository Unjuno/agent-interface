"""Portable raw-only audit for the retained A04 child-pipe construction."""
from pathlib import Path
import hashlib, json, subprocess
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def git_blob(commit, path):
    return subprocess.check_output(["git", "rev-parse", f"{commit}:{path}"], cwd=ROOT, text=True).strip()

def verify():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    commits = freeze["immutable_git_commits"]
    for label, paths in freeze["git_blobs"].items():
        commit = commits[label]
        for path, expected in paths.items():
            actual = git_blob(commit, path)
            assert actual == expected, f"Git blob mismatch: {label}:{path}"
    for rel, expected in freeze["files"].items():
        assert hashlib.sha256((HERE / rel).read_bytes()).hexdigest() == expected, f"frozen file hash mismatch: {rel}"
    result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
    arms = {row["arm"]: row for row in result["arms"]}
    assert result["main_sha"] == commits["main_source_snapshot"]
    assert result["candidate_sha"] == commits["candidate"]
    assert result["decision"] == "PASS_V39_SELECTION_V15_CHILD_PIPE_SCOPED"
    for row in arms.values():
        assert Path(row["selected_command"][1]).name == "session_map01_v15.py"
        raw = HERE / "results" / row["arm"]
        stdout = (raw / "child-stdout.jsonl").read_text(encoding="utf-8").splitlines()
        stderr = (raw / "child-stderr.txt").read_text(encoding="utf-8")
        assert stdout == row["stdout_lines"] and stderr == row["stderr"]
        events = [json.loads(line) for line in stdout]
        assert events and events[0]["event"] == "ready"
        commands = [event for event in events if event.get("event") == "command"]
        assert commands == row["command_events"]
        summary = json.loads((raw / "scorer" / "scorer-summary.json").read_text(encoding="utf-8"))
        assert summary["scheduler"] == row["scheduler"]
    base, candidate = arms["baseline"], arms["candidate"]
    assert base["exit_code"] != 0 and "WinError 10093" in base["stderr"] and not base["command_events"]
    assert candidate["exit_code"] == 0 and candidate["sent_delayed_command"]
    assert len(candidate["command_events"]) == 1
    event = candidate["command_events"][0]
    assert json.loads(event["line"]) == event["parsed_command"] == {"op": "finish"}
    assert event["command_thread_id"] == event["polling_owner_thread_id"] == candidate["ready_event"]["owner_thread_id"]
    assert event["sample_thread_ids"] and set(event["sample_thread_ids"]) == {event["command_thread_id"]}
    assert event["periodic_samples"] >= 2
    assert candidate["scheduler"]["samples"] == event["periodic_samples"]
    print("PASS_AUDIT_SCOPED")
    return True

if __name__ == "__main__":
    verify()
