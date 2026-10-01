"""One fixed initial/resume runner contract pair; never calls a model."""
import hashlib
import json
import os
import pathlib
import subprocess
import sys

root = pathlib.Path(__file__).parent
runroot = root / "candidate-output"
runroot.mkdir(exist_ok=False)
fake_log = runroot / "fake-cli.jsonl"
(runroot / "image.bin").write_bytes(b"fixed-image-fixture")
(runroot / "instructions.txt").write_text("fixture instructions\n", encoding="utf-8")
(runroot / "schema.json").write_text('{"type":"object"}\n', encoding="utf-8")
prompts = [
    "Select the next bounded MAP01 action.\nPrevious no-visible-effect actions: []\n",
    'Select the next bounded MAP01 action.\nPrevious no-visible-effect actions: ["forward"]\n',
]
for i, prompt in enumerate(prompts, start=1):
    (runroot / f"prompt-{i}.txt").write_text(prompt, encoding="utf-8")

env = dict(os.environ)
env["FAKE_CLI_LOG"] = str(fake_log)
session = "-"
runs = []
for i in (1, 2):
    out = runroot / ("initial" if i == 1 else "resume")
    command = [
        sys.executable, str(root / "runner_v2.py"), sys.executable,
        str(root / "fake_cli.py"), str(runroot / f"prompt-{i}.txt"),
        str(runroot), str(out), str(runroot / "image.bin"),
        str(runroot / "instructions.txt"), str(runroot / "schema.json"),
        session, "fixture-model", "low",
    ]
    cp = subprocess.run(command, cwd=runroot, env=env, capture_output=True, text=True)
    (runroot / f"wrapper-stdout-{i}.txt").write_text(cp.stdout, encoding="utf-8")
    (runroot / f"wrapper-stderr-{i}.txt").write_text(cp.stderr, encoding="utf-8")
    runs.append({"call": i, "returncode": cp.returncode, "session_argument": session})
    if cp.returncode != 0:
        break
    if i == 1:
        events = [json.loads(row) for row in (out / "events.jsonl").read_text().splitlines()]
        threads = [row["thread_id"] for row in events if row.get("type") == "thread.started"]
        if len(threads) != 1:
            break
        session = threads[0]

result = {
    "runs": runs,
    "runner_git_blob_sha": "a6f51c7e92f06213c97978889bb029ac1b581dfc",
    "runner_sha256": hashlib.sha256((root / "runner_v2.py").read_bytes()).hexdigest(),
    "fake_cli_sha256": hashlib.sha256((root / "fake_cli.py").read_bytes()).hexdigest(),
    "candidate_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
    "session_id_derived_from_initial_thread_started": session,
}
(runroot / "candidate-result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
