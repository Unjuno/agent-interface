"""Independent raw-only check of the fake-CLI runner boundary trace."""
import hashlib
import json
import pathlib

root = pathlib.Path(__file__).parent
runroot = root / "candidate-output"
rows = [json.loads(line) for line in (runroot / "fake-cli.jsonl").read_text(encoding="utf-8").splitlines()]
result = json.loads((runroot / "candidate-result.json").read_text(encoding="utf-8"))
initial = rows[0]
resume = rows[1]
runner_sha = hashlib.sha256((root / "runner_v2.py").read_bytes()).hexdigest()
assert len(rows) == 2
assert initial["argv"][0] == "exec"
assert initial["argv"][-1] == "-"
assert resume["argv"][:2] == ["exec", "resume"]
assert resume["argv"][-2:] == ["fixture-thread-5791", "-"]
assert initial["prompt"] == (runroot / "prompt-1.txt").read_text(encoding="utf-8")
assert resume["prompt"] == (runroot / "prompt-2.txt").read_text(encoding="utf-8")
assert "Previous no-visible-effect actions: []" in initial["prompt"]
assert 'Previous no-visible-effect actions: ["forward"]' in resume["prompt"]
assert result["runner_git_blob_sha"] == "a6f51c7e92f06213c97978889bb029ac1b581dfc"
assert result["runner_sha256"] == runner_sha
assert result["session_id_derived_from_initial_thread_started"] == "fixture-thread-5791"
for name, thread_id, mode in [
    ("initial", "fixture-thread-5791", "initial"),
    ("resume", "fixture-thread-5791", "resume"),
]:
    out = runroot / name
    events = [json.loads(line) for line in (out / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
    process = json.loads((out / "process.json").read_text(encoding="utf-8"))
    assert [e["thread_id"] for e in events if e.get("type") == "thread.started"] == [thread_id]
    assert plan["mode"] == mode
    assert plan["runner_sha256"] == runner_sha
    assert process["exit_code"] == 0
print(json.dumps({
    "audit": "PASS_STUBBED_RUNNER_RESUME_AND_PROMPT_FORWARDING",
    "runner_sha256": runner_sha,
    "fake_cli_invocations": len(rows),
    "same_session_id": True,
    "explicit_effect_feedback_forwarded_on_resume": True,
    "provider_transcript_semantics": "UNTESTED",
}, sort_keys=True))
