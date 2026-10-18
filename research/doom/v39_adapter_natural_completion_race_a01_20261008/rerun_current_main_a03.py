import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "FREEZE_A03.json").read_text(encoding="utf-8"))
TEMP = pathlib.Path(tempfile.mkdtemp(prefix="v39-reader-a03-", dir=ROOT.parents[3]))
try:
    (TEMP / "source").mkdir()
    for row in FREEZE["sources"]:
        raw = subprocess.check_output(["git", "show", f"{FREEZE['main_commit']}:{row['path']}"], cwd=ROOT)
        git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        assert git_blob == row["git_blob"], (row["path"], git_blob, row["git_blob"])
        (TEMP / "source" / row["local"]).write_bytes(raw)
    harness = (ROOT / "run_reader_race_a02.py").read_text(encoding="utf-8")
    harness = harness.replace("FREEZE_A02.json", "FREEZE.json").replace("RESULT_A02.json", "RESULT.json")
    (TEMP / "run.py").write_text(harness, encoding="utf-8")
    frozen = {
        "main_commit": FREEZE["main_commit"],
        "sources": FREEZE["sources"],
    }
    (TEMP / "FREEZE.json").write_text(json.dumps(frozen), encoding="utf-8")
    run = subprocess.run([sys.executable, "-B", "run.py"], cwd=TEMP, check=True, capture_output=True, text=True)
    result = json.loads((TEMP / "RESULT.json").read_text(encoding="utf-8"))
    assert result["status"] == "PASS_EXACT_READER_ROUTES_COMPLETION_BEFORE_INTERRUPT_REPLY"
    assert result["completion_consumed_before_interrupt_response"] is True
    assert result["turn_result"]["answer_eligible"] is False
    assert result["turn_result"]["answer"] is None
    assert result["helper_terminal"]["release"] == {"verified": True, "keys_down": [], "buttons_down": []}
    raw_result = (TEMP / "RESULT.json").read_bytes()
    stored = json.loads((ROOT / "RESULT_A03.json").read_text(encoding="utf-8"))
    event_names = lambda doc: [row["event"] for row in doc["events"]]
    assert result["main"] == stored["main"] == FREEZE["main_commit"]
    assert result["source_blobs"] == stored["source_blobs"]
    assert event_names(result) == event_names(stored)
    assert result["turn_result"] == stored["turn_result"]
    assert result["helper_terminal"] == stored["helper_terminal"]
    digest = hashlib.sha256(raw_result).hexdigest()
    stored_digest = hashlib.sha256((ROOT / "RESULT_A03.json").read_bytes()).hexdigest()
    print(json.dumps({"status": "PASS_CURRENT_MAIN_A03_RERUN", "main_commit": FREEZE["main_commit"], "candidate_result_sha256": digest, "retained_result_sha256": stored_digest, "event_count": len(result["events"]), "retained_artifact_unchanged": True}))
finally:
    shutil.rmtree(TEMP, ignore_errors=True)
